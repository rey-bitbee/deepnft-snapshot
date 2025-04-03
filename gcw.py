from collections import defaultdict

from loguru import logger
from web3 import Web3

from ethereum import get_erc721_snapshot, get_erc721_snapshot_by_ids, get_contract
from googlesheet import write_to_sheet
from yayasea import get_listing


def get_unlist_legendary_gcws(rpc: str):
    ids = [
        6,
        10,
        12,
        117,
        1575,
        2628,
        2855,
        7006,
        7225,
        8908,
        3323,
        5676,
        5765,
        8607,
        8707,
        9199,
    ]
    ids.sort()
    ids = tuple(ids)

    token_address = "0x4D9325A306f5D07d89eC7C92dE238ac6434cDEd3"
    w3 = Web3(Web3.HTTPProvider(rpc))
    contract = get_contract(w3, token_address, "abi/ERC721.json")

    block_number = w3.eth.get_block_number()
    snapshot = get_erc721_snapshot_by_ids(contract, block_number, ids)

    list_ids = get_listing(
        collection_name="GoldenCicadaWarrior",
        extra_params={"traits": "W3siayI6NiwidiI6WzFdfV0="}
    )
    result = defaultdict(list)
    for token_id, owner in snapshot.items():
        if token_id in list_ids:
            continue
        result[owner].append(token_id)

    return result


def get_unlist_gcws(rpc, spreadsheet_id, div, mod, unlist_sheet, result_sheet, end_token_id=None):
    token_address = "0x4D9325A306f5D07d89eC7C92dE238ac6434cDEd3"
    w3 = Web3(Web3.HTTPProvider(rpc))
    contract = get_contract(w3, token_address, "abi/ERC721.json")

    block_number = w3.eth.get_block_number()
    snapshot = get_erc721_snapshot(contract, block_number, 1, worker_size=50, end_token_id=end_token_id)
    logger.info("snapshot count: {}", len(snapshot))

    list_ids = get_listing(
        collection_name="GoldenCicadaWarrior",
    )
    logger.info("list_ids: {}", list_ids)

    unlist_sheet_rows = []
    unlist_sheet_header = ["id", "owner"]
    unlist_sheet_rows.append(unlist_sheet_header)

    result_sheet_rows = []
    result_sheet_header = ["owner", "amount"]
    result_sheet_rows.append(result_sheet_header)

    result = defaultdict(list)
    token_count = 0
    for token_id, owner in snapshot.items():
        if token_id in list_ids:
            continue

        unlist_sheet_rows.append([token_id, owner])
        if not (token_id % div == mod):
            continue

        token_count += 1

        result[owner].append(token_id)

    for owner, token_ids in result.items():
        result_sheet_rows.append([owner, len(token_ids)])

    logger.info("snapshot count: {}", len(snapshot))
    logger.info("listing count: {}", len(list_ids))
    logger.info("token count: {}", token_count)
    logger.info("owner count: {}", len(result))

    write_to_sheet(spreadsheet_id, f"{unlist_sheet}!A1:B{len(unlist_sheet_rows)}", unlist_sheet_rows)
    write_to_sheet(spreadsheet_id, f"{result_sheet}!A1:B{len(result_sheet_rows)}", result_sheet_rows)

    title = "GCW快照通知"
    text = f"### *{title}* \n "
    text += f"### [快照文件](https://docs.google.com/spreadsheets/d/{spreadsheet_id}) \n "
    text += f"### 发行量: {len(snapshot)} \n "
    text += f"### 挂单数量: {len(list_ids)} \n "
    text += f"### 快照token数量: {token_count} \n "
    text += f"### 快照owner数量: {len(result)} \n "

    return {
        "msg_type": "markdown",
        "title": title,
        "text": text,
    }
