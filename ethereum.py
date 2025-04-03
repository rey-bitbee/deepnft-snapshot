from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import time
from typing import Tuple

from loguru import logger
from web3 import Web3

from utils import get_progress_bar


def get_contract(w3, address, abi_path):
    abi = json.load(Path(abi_path).open())
    return w3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)


def get_owner(contract, token_id, block_number):
    try:
        owner = contract.functions.ownerOf(token_id).call(block_identifier=block_number)
        # logger.debug("Owner of token {}: {}", token_id, owner)
        return token_id, owner
    except Exception as e:
        logger.error("Error getting owner for token {}: {}", token_id, e)
        return token_id, None


def get_erc721_snapshot(contract, block_number, start_token_id: int = 0, worker_size: int = 100, end_token_id: int = None) -> dict:
    if not end_token_id:
        total_supply = contract.functions.totalSupply().call(block_identifier=block_number)
        logger.info("Total supply: {}", total_supply)
        end_token_id = start_token_id + total_supply - 1

    start = time.perf_counter()
    owner_dict = {}

    logger.info("Fetching token[{}, {}] owner on block {}...", start_token_id, end_token_id, block_number)
    with get_progress_bar(end_token_id - start_token_id + 1) as bar:
        with ThreadPoolExecutor(max_workers=worker_size) as executor:
            futures = [
                executor.submit(get_owner, contract, token_id, block_number)
                for token_id in range(start_token_id, end_token_id + 1)
            ]
            for future in as_completed(futures):
                bar()
                token_id, owner = future.result()
                if owner:
                    owner_dict[token_id] = owner
                else:
                    raise Exception(f"Failed to get owner for token {token_id}")

    logger.info("Owner snapshot time taken: {}s", time.perf_counter() - start)
    return owner_dict


def get_erc721_snapshot_by_ids(contract, block_number, ids: Tuple[int], worker_size: int = 100) -> dict:
    start = time.perf_counter()
    owner_dict = {}

    logger.info("Fetching tokens owner on block {}...", block_number)
    with get_progress_bar(len(ids)) as bar:
        with ThreadPoolExecutor(max_workers=worker_size) as executor:
            futures = [
                executor.submit(get_owner, contract, token_id, block_number)
                for token_id in ids
            ]
            for future in as_completed(futures):
                bar()
                token_id, owner = future.result()
                if owner:
                    owner_dict[token_id] = owner
                else:
                    raise Exception(f"Failed to get owner for token {token_id}")

    logger.info("Owner snapshot time taken: {}s", time.perf_counter() - start)
    return owner_dict