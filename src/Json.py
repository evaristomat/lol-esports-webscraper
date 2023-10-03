import copy
import os
from typing import List, Dict, Set

from src.Dtos import GameDetailDto, GameOverviewDto
from src.Utils import flatmap


def join_jsons(jsons: List[List[GameDetailDto]]) -> List[GameDetailDto]:
    fixed_json: Dict[GameOverviewDto, GameDetailDto] = {}
    changed_jsons: Set[GameDetailDto] = set()

    def get(detail_dto: GameDetailDto) -> GameDetailDto:
        if detail_dto.overview not in fixed_json:
            fixed_json[detail_dto.overview] = copy.deepcopy(detail_dto)
        return fixed_json[detail_dto.overview]

    flat_jsons: Set[GameDetailDto] = set(flatmap(lambda x: x, jsons))

    def merge(variable: str, json: GameDetailDto):
        stored_json = get(json)
        setattr(stored_json, variable, list(set(getattr(stored_json, variable)) | set(getattr(json, variable))))

    for local_json in flat_jsons:
        previous = copy.deepcopy(get(local_json))
        merge("winner", local_json)
        merge("first_blood", local_json)
        merge("first_kill_baron", local_json)
        merge("first_destroy_inhibitor", local_json)
        merge("kill_handicap", local_json)
        merge("total_kills", local_json)
        merge("total_towers", local_json)
        merge("total_dragons", local_json)
        merge("total_barons", local_json)
        merge("total_inhibitors", local_json)
        if previous != get(local_json):
            changed_jsons.add(local_json)

    return list(fixed_json.values())


def write_as_json_to_file(file_path: str, content: List[GameDetailDto]):
    with open(file_path, "w+") as f:
        print(file_path, content)
        print(GameDetailDto.schema().dumps(content, many=True))
        f.write(GameDetailDto.schema().dumps(content, many=True, indent=4))


def read_json(file_path) -> List[GameDetailDto]:
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return GameDetailDto.schema().loads(content, many=True)
