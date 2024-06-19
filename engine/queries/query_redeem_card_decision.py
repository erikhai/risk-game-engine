from typing import Iterable, Literal

from engine.models.player.player_public_model import PlayerPublicModel
from engine.models.territory_model import TerritoryModel
from engine.queries.base_query import BaseQuery


class QueryRedeemCardDecision(BaseQuery):
    query_type: Literal["player_decision"] = "player_decision"
    territories: Iterable[TerritoryModel]
    players: Iterable[PlayerPublicModel]