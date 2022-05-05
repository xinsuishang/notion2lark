#!/usr/bin/env python3
# coding=utf-8

import time
import sys

sys.path.append("../lark")
sys.path.append("../notion")

from lark_calendar import create_calendar_events, patch_calendar_events
from notion_database import database_query, page_update
from settings_sync import DATA_MAP

cache = {}


def database_check(conf_key, next_cursor=None, all=False):
    """
    获取 notion database，并检查本地缓存
    """
    database_id = DATA_MAP[conf_key]
    resp = database_query(database_id, next_cursor, all)

    print(f"{conf_key} 共需处理 {len(resp['results'])} 条")
    idx = 0
    for cur_data in resp["results"]:
        idx += 1
        print(f"{conf_key} 开始处理第 {idx} 条")
        cur_start = time.time()

        page_id = cur_data["id"]
        properties = cur_data["properties"]
        if page_id in cache[database_id] and cache[database_id][page_id]["last_edited_time"] == \
                cur_data["last_edited_time"]:
            rich_text = properties.get("lark_event_id", {}).get("rich_text", [])
            if len(rich_text):
                lark_event_id = rich_text[0]["text"]["content"]
                if lark_event_id:
                    print(f"[{page_id}]版本未发生变化，无需更新")
                else:
                    last_edited_time = page_update(page_id, lark_event_id).get("last_edited_time")
                    if last_edited_time:
                        cache[database_id][page_id]["last_edited_time"] = last_edited_time
        else:
            # 时间获取
            cur_type = properties["Date"]["type"]
            if cur_type == "formula":
                element = properties["Date"][cur_type]
                element_type = element["type"]
                start_time = end_time = element[element_type]
            else:
                start_time = properties["Date"][cur_type]["start"]
                end_time = properties["Date"][cur_type]["end"]

            title = properties["Name"]["title"][0]["text"]["content"]
            description = cur_data["url"]

            if title is None:
                continue
            if start_time is None and end_time is None:
                continue

            # 飞书日历处理
            rich_text = properties.get("lark_event_id", {}).get("rich_text", [])
            if len(rich_text):
                lark_event_id = rich_text[0]["text"]["content"]
                patch_calendar_events(title, description, start_time, end_time, lark_event_id)
                cache[database_id][page_id] = {
                    "last_edited_time": cur_data["last_edited_time"],
                    "lark_event_id": lark_event_id
                }
            else:
                lark_event_id = create_calendar_events(title, description, start_time, end_time)

                # 版本存储
                cache[database_id][page_id] = {
                    "last_edited_time": cur_data["last_edited_time"],
                    "lark_event_id": lark_event_id
                }
                # notion 版本回写
                last_edited_time = page_update(page_id, lark_event_id).get("last_edited_time")
                if last_edited_time:
                    cache[database_id][page_id]["last_edited_time"] = last_edited_time
        cur_end = time.time()
        print(f"{conf_key} 第 {idx} 条处理完成，完成时间：{int(cur_end)}, 耗时： {int(cur_end * 1000 - cur_start * 1000) / 1000}s")
    if resp["has_more"]:
        database_check(conf_key, next_cursor=resp["next_cursor"], all=all)


def cache_init():
    for database_id in DATA_MAP.values():
        if not cache.get(database_id):
            cache[database_id] = dict()


def main():
    cache_init()
    for k, value in DATA_MAP.items():
        print(f"开始处理：{k}")
        print(cache[value])
        cur_start = time.time()
        print(f"{k} 开始处理，处理时间：{int(start)}")
        if not cache[value]:
            # 没有本地缓存，认为是第一次启动，查询所有
            database_check(k, all=True)
        else:
            try:
                database_check(k)
            except Exception as e:
                print(e)
        cur_end = time.time()
        print(f"{k} 处理完成，完成时间：{int(cur_end)}, 耗时： {cur_end - cur_start}s")


if __name__ == "__main__":
    start = time.time() - 86400 * 100
    while True:
        now = time.time()
        if now - 60 > start:
            # 60s 检查一次，如果不到 60s，sleep 10s
            start = now
            try:
                main()
            except Exception as e:
                print("处理异常")
                print(e)
                for v in cache.values():
                    v.clear()
        else:
            time.sleep(10)
