from typing import List, Tuple, Any

import numpy as np
from lightfm import LightFM
from lightfm.data import Dataset
from PO.user import User
from PO.merchant_meta import MerchantMeta as DB_MerchantMeta,CATEGORIES
from PO.user import User as DB_User
from PO.follow_relation import FollowRelation
from PO.comment2promotion import Comment2Promotion
from PO.comment2merchant import Comment2Merchant
from PO.like2promotion import Like2Promotion
from PO.promotion import Promotion
from snownlp import SnowNLP
from utils.distance_util import haversine_distance

class Recommend:
    __dataset: Dataset
    __model: LightFM
    # 权重
    __USER_FEATURES = {'gender': 3, 'age': 2}
    __INTERACTION_WEIGHTS = {"follow": 10, "comment2promotion": 1, "comment_text2merchant": 3, "like2promotion": 0.5,'comment_star2merchant':2}

    def __translate_user(self, user: User):
        if user.age <= 35:
            age_type = "young"
        elif user.age <= 55:
            age_type = "medium"
        else:
            age_type = "old"
        return (user.id, {f"gender:{user.gender}": self.__USER_FEATURES['gender'],
                          f"age:{age_type}": self.__USER_FEATURES['age']})

    def __translate_merchant(self, merchant: DB_MerchantMeta):
        user = DB_User.select().where(DB_User.id==merchant.user_id).first()

        # 评论数量
        if merchant.comment_num <= 50:
            comment_type = "little"
        elif merchant.comment_num <= 120:
            comment_type = "medium"
        else:
            comment_type = "big"
        # 推广数量
        if merchant.promotion_num <= 40:
            promotion_type = "little"
        elif merchant.promotion_num <= 80:
            promotion_type = "medium"
        else:
            promotion_type = "big"
        # 粉丝数量
        if user.fan_num <= 250:
            fan_type = "little"
        elif user.fan_num <= 1000:
            fan_type = "medium"
        else:
            fan_type = "big"
        return (
            merchant.user_id,
            [f"category:{merchant.category}", f"comment:{comment_type}", f"promotion:{promotion_type}",
             f"fan:{fan_type}"])

    def __get_users(self) -> list:
        db_users = list(User.select())
        self.__users = db_users
        users = list(map(self.__translate_user, db_users))
        return users

    def __get_merchants(self):
        db_merchants = list(DB_MerchantMeta.select())

        return list(map(self.__translate_merchant, db_merchants))

    def __get_interaction(self) -> List[Tuple[str | int, str | int, int | float]]:
        # user_id_map, user_feature_map, merchant_id_map, item_feature_map = self.__dataset.mapping()
        def add_interaction(user_id, item_id, diff):
            # key = f"{user_id_map[user_id]}:{merchant_id_map[item_id]}"
            key = f"{user_id}:{item_id}"
            interaction.setdefault(key, 0)
            interaction[key] += diff

        interaction = {}
        # 关注情况
        db_follows = list(FollowRelation.select())
        # TODO 切换为内部id
        for f in db_follows:
            add_interaction(f.fan_id, f.user_id, self.__INTERACTION_WEIGHTS['follow'])
        # 点赞情况
        db_like2promotion = list(Like2Promotion.select())
        for like in db_like2promotion:
            add_interaction(like.user_id, like.merchant_id,
                            self.__INTERACTION_WEIGHTS['like2promotion'])
        # 点赞情况
        db_comment2promotion = list(Comment2Promotion.select())
        for comment in db_comment2promotion:
            score = SnowNLP(comment.text).sentiments
            add_interaction(comment.user_id, comment.merchant_id,
                            score * self.__INTERACTION_WEIGHTS['comment2promotion'])
        db_comment2merchant = list(Comment2Merchant.select())
        for comment in db_comment2merchant:
            text_score = SnowNLP(comment.text).sentiments * self.__INTERACTION_WEIGHTS['comment_text2merchant']
            star_score = comment.star * self.__INTERACTION_WEIGHTS['comment_star2merchant']
            add_interaction(comment.user_id, comment.merchant_id,
                            text_score+star_score)
        interactions = []
        user_id_map, user_feature_map, merchant_id_map, item_feature_map = self.__dataset.mapping()
        merchant_ids = merchant_id_map.keys()
        for k, score in interaction.items():
            user_id, item_id = k.split(":")
            user_id, item_id = int(user_id), int(item_id)
            # 排除user和user交互的情况
            if item_id not in merchant_ids:
                continue
            interactions.append((user_id, item_id, score))
        return interactions

    def create_internal_id(self, user_ids: list = None, merchant_ids: list = None, user_features: list = None,
                           merchant_features: list = None):
        self.__dataset.fit_partial(users=user_ids, items=merchant_ids, user_features=user_features,
                                   item_features=merchant_features)

    def train(self):
        users = self.__get_users()
        merchants = self.__get_merchants()
        # 先创建内部id
        # print("创建内部id")
        self.create_internal_id(user_ids=[u[0] for u in users], user_features=[f for u in users for f in u[1]],
                                merchant_ids=[m[0] for m in merchants],
                                merchant_features=[f for m in merchants for f in m[1]])
        # 交互矩阵需要用到内部id
        # print("获得交互")
        interaction = self.__get_interaction()
        # 再创建各个特征值
        # print("创建特征值")
        uf = self.__dataset.build_user_features(users)
        itf = self.__dataset.build_item_features(merchants)
        (interactions, weights) = self.__dataset.build_interactions(interaction)
        # print("开始训练")
        self.__model.fit(interactions, user_features=uf, item_features=itf, sample_weight=weights, epochs=10)
        print("训练结束")

    def __init__(self):
        self.__dataset = Dataset()
        self.__model = LightFM(loss='logistic')
        self.train()

    def __predict(self, user_id,item_ids) -> list:
        user_id_map, _, _, _ = self.__dataset.mapping()
        # 预测现有的用户
        # 注意输入的id必须要转换为lightfm内部的id
        user_x = user_id_map[user_id]
        res = self.__model.predict(user_x, item_ids)
        # 注意获得的顺序是item_id_map里的顺序
        res = list(zip(item_ids, res))
        return res

    def predict(self, user_id, latitude: float, longitude: float,category:str=None, top_k=20):
        user_id_map, user_feature_map, item_id_map, item_feature_map = self.__dataset.mapping()

        if category is None:
            item_ids = np.arange(len(item_id_map))
            merchants_data = DB_MerchantMeta.select(DB_MerchantMeta.user_id, DB_MerchantMeta.location)
        else:
            assert category in CATEGORIES
            merchants_data = DB_MerchantMeta.select(DB_MerchantMeta.user_id, DB_MerchantMeta.location).where(DB_MerchantMeta.category==category)
            item_ids = []
            for merchant_id,internal_idx in item_id_map.items():
                if merchant_id in [x.user_id for x in merchants_data]:
                    # 只取分类内的item
                    item_ids.append(internal_idx)
        res: List[int, float] = self.__predict(user_id,item_ids)
        merchant_location = {}
        for datum in merchants_data:
            merchant_location[item_id_map[datum.user_id]] = datum.location
        new_res = []
        item_id_list = list(item_id_map.items())
        for internal_idx, score in res:
            # print(score)
            merchant_id = item_id_list[internal_idx][0]
            location = merchant_location[internal_idx]
            kilo = haversine_distance(latitude, longitude, location[0], location[1]) / 1000
            # 离得越远扣的越多
            new_score = score - kilo *0.01
            new_res.append((merchant_id,new_score))
        new_res = sorted(new_res, key=lambda x: x[1], reverse=True)[:top_k]
        return [x[0] for x in new_res]

    def evaluate(self):
        from lightfm.evaluation import auc_score
        interaction = self.__get_interaction()
        (interactions, weights) = self.__dataset.build_interactions(interaction)
        users = self.__get_users()
        merchants = self.__get_merchants()
        uf = self.__dataset.build_user_features(users)
        itf = self.__dataset.build_item_features(merchants)
        train_auc = auc_score(self.__model, interactions, user_features=uf, item_features=itf).mean()
        print('Hybrid training set AUC: %s' % train_auc)

rec = Recommend()

def get_recommend_merchant_ids(user_id,latitude,longitude,category=None)->List[int]:
    # 推荐的商家
    recommend_merchant_ids: List[int] = rec.predict(user_id, latitude, longitude,category)
    return recommend_merchant_ids

def retrain():
    rec.train()