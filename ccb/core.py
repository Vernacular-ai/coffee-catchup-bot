import math
from typing import List

import slack
from pydash import py_
from tqdm import tqdm

from ccb.types import User


def load_users_from_user_group(client: slack.WebClient, user_group: str) -> List[User]:
    """
    List users in a given user group handle.
    """

    user_groups = client.usergroups_list(include_users=True)["usergroups"]
    group = py_.find(user_groups, lambda it: it["handle"] == user_group)
    user_ids = group["users"]

    users = []
    for i in tqdm(user_ids, desc=f"Collecting user info for group {user_group}"):
        u = client.users_info(user=i)["user"]
        users.append(User(u["id"], u["real_name"], u["tz"]))

    return users


def load_users(client: slack.WebClient) -> List[User]:
    """
    List workspace users.
    """

    response = client.users_list()
    members = response["members"]

    users = []
    for member in members:
        if member["is_bot"]:
            continue
        if member["deleted"]:
            continue
        if member["id"] == "USLACKBOT":
            continue
        users.append(User(member["id"], member["real_name"], u["tz"]))
    return users


def group_items(items: List, n: int) -> List[List]:
    """
    Group items in group of max size n. More larger groups are preferred
    instead of less smaller ones.
    """

    n_groups = math.ceil(len(items) / n)

    base_size = (len(items) // n_groups) + 1
    base_n_groups = len(items) % n_groups

    rest_size = base_size - 1
    rest_n_groups = n_groups - base_n_groups

    groups = []

    start = 0
    for _ in range(base_n_groups):
        end = start + base_size
        groups.append(items[start:end])
        start = end

    for _ in range(rest_n_groups):
        end = start + rest_size
        groups.append(items[start:end])
        start = end

    return groups


def channel_name_to_id(name: str, client: slack.WebClient) -> str:
    """
    Return slack id for given channel name.
    """

    response = client.users_conversations(types="public_channel,private_channel,mpim,im", exclude_archived=True)
    channels = response["channels"]

    result = py_.find(channels, lambda ch: ch["name"] == name)

    if result:
        return result["id"]
    else:
        raise ValueError(f"Channel {name} not found")
