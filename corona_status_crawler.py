
from urllib.request import urlopen
from bs4 import BeautifulSoup
import os
import datetime
import copy
import time
import sys


''' Example of item log (in csv file)
#item 19
0) 시도:        대전
1) 시군구:      유성구
2) 장소유형:    아울렛
3) 상호명:      모다아울렛 대전점
4) 주소:        유성구 대정로 5(대정동)
5) 노출일시:    12.20.(일) 14:30~14:50
6) 소독여부:    소독예정
'''

field_names = ["시도", "시군구", "장소유형", "상호명", "주소", "노출일시", "소독여부", "비고"]


def read_record_from(record_url) -> [[str]]:
    ### rec_table is a list of items, where an item is a list of data fields
    rec_table = []
    item_cnt = 0
    if os.path.exists(record_url):
        print("Read the record file...", record_url)
        fread = open(record_url, mode='r', encoding='utf-8')
        rec_lines = fread.readlines()
        rec_lines = [line for line in rec_lines if len(line.strip()) > 0]
        for line in rec_lines:
            if line.startswith("###"):
                continue
            elif line.startswith("#revision:"):
                global update_cnt
                update_cnt = int(line.split()[1])
            elif line.startswith("#item"):
                rec_table.append([line.strip()])
                item_cnt += 1
            else:
                field_content = line.split(maxsplit=2)[2].strip()
                rec_table[item_cnt - 1].append([field_content])
        fread.close()
    else:
        print("Create a new record file...", record_url)
        fwrite = open(record_url, mode='x', encoding='utf-8')
        fwrite.write("### Corona Status Log ###\n")
        fwrite.close()
    print("Reading record file done.")
    return rec_table


def make_webpage_table_from(webpage_url) -> [[str]]:
    html = urlopen(webpage_url)
    bsObject = BeautifulSoup(html, "html.parser")
    webpage_table = []

    corona_table = bsObject.body.find("table", {"class": "corona"})
    for content in [content for content in corona_table.contents if content.name == "tbody"]:
        item_raw_list = [item for item in content.contents if item.name == "tr"]
        # print("웹페이지의 총 항목 개수:", len(item_raw_list))
        for item_raw in item_raw_list:
            field_raw_list = [field_raw for field_raw in item_raw.contents if field_raw.name == "td"]
            is_blinded = len(field_raw_list) != len(field_names)
            # print("item# %d:"%item_cnt, len(field_list), " -->", "Blinded" if blinded else "Visible")
            if not is_blinded:
                field_info_list = ["#item"]
                for i, field_raw in enumerate(field_raw_list):
                    field_text = field_raw.text.strip().replace('\n', ' ').replace('\t', ' ').replace('\r', '')
                    if field_text != "":
                        field_info_list.append([field_text])
                webpage_table.append(field_info_list)
    # print("웹페이지의 공개 항목 개수:", len(webpage_table))
    # for item in webpage_table:
    #     print(item[0])
    #     for i, field in enumerate(item[1:]):
    #         print("{}) {}:\t{}".format(i, field_names[i], field[0]))
    #     print("\n")
    print("웹페이지 정보 읽기 완료.")
    return webpage_table


def get_field_value_of(table_item, field_name) -> str:
    global field_names
    for field_num, name in enumerate(field_names):
        if name == field_name:
            return table_item[field_num][0]
    raise ValueError("Invalid field name requested to function get_field_value().")


def make_record_update_from(old_table, new_table):
    update_table = []
    for new_item in new_table:
        is_new_item = True
        for old_item in old_table:
            if get_field_value_of(new_item, "상호명") == get_field_value_of(old_item, "상호명")\
                    and get_field_value_of(new_item, "주소") == get_field_value_of(old_item, "주소")\
                    and get_field_value_of(new_item, "노출일시") == get_field_value_of(old_item, "노출일시"):
                ### 동일 item으로 판단됨. old_table 검색 중지. (TODO: 소독여부 field는 업데이트 하도록 구현할 것)
                is_new_item = False
                break
        if is_new_item is True:
            print("Adding new item...")
            print(new_item)
            update_table.append(new_item)
    return update_table


update_cnt = 0
def write_update_to(record_url, update_table) -> int:
    if len(update_table) > 0:
        global update_cnt
        update_cnt += 1
        fwrite = open(record_url, mode='a', encoding='utf-8')
        for item in update_table:
            print(item[0] + " %d" % update_cnt)
            fwrite.write(item[0] + " %d\n" % update_cnt)
            for i, field in enumerate(item[1:]):
                print("{}\t{}\t{}".format(i, field_names[i], field[0]))
                fwrite.write("{}\t{}\t{}\n".format(i, field_names[i], field[0]))
            print("\n")
            fwrite.write("\n")
        print("#revision: %d\n\n" % update_cnt)
        fwrite.write("#revision: %d\n#timestamp: %s\n\n" % (update_cnt, datetime.datetime.now()))
        fwrite.close()
        #print("새로운 항목 %d개가 추가되었습니다." % len(update_table))
    #else:
        #print("새로운 항목 없음")
    return len(update_table)


def countdowner(sec_to_go):
    while sec_to_go:
        sec_to_go -= 1
        min, sec = divmod(sec_to_go, 60)
        print("\r다음 업데이트까지 남은 시간: {:02d}분 {:02d}초".format(min, sec), end='')
        time.sleep(1)
    print("\n")



if len(sys.argv) < 2:
    print("You need param of update interval.\nUsage: python Corona_status_crawler.py <update_interval_in_minute>")
    update_interval_minute = 30 ### default update interval
else:
    update_interval_minute = sys.argv[1]
    if update_interval_minute.isnumeric() is False:
        print("Update interval should be positive decimal integer.")
        exit(1)
    update_interval_minute = int(update_interval_minute)
update_interval_minute = 30 if update_interval_minute <= 0 else update_interval_minute

print("Start to log Corona19 status report from Daejeon website, every %s minutes." % update_interval_minute)
rec_filename = "corona_status_record.csv"
old_table = read_record_from(rec_filename)
while True:
    new_table = make_webpage_table_from("https://www.daejeon.go.kr/corona19/index.do?menuId=0008")
    update_table = make_record_update_from(old_table, new_table)
    updated_item_cnt = write_update_to(rec_filename, update_table)
    if updated_item_cnt > 0:
        result_msg = "업데이트 %d차 (%d개 항목 추가)" % (update_cnt, updated_item_cnt)
    else:
        result_msg = "업데이트 항목 없음"
    print("%s - 코로나19 현황 업데이트 완료. 갱신일시: %s" % (result_msg, datetime.datetime.now()))
    old_table = copy.deepcopy(new_table)
    countdowner(update_interval_minute * 60)

