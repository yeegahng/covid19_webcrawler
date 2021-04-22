import numpy as np

prefix = ["1.시군구", "2.장소유형", "3.상호명", "4.주소", "5.노출일시", "6.소독여부", "7.비고"]

rfile = open("C:\\Users\LGRnD\Desktop\covid19_daejeon.txt", 'r', encoding='utf-8')
wfile = open("C:\\Users\LGRnD\Desktop\covid19_daejeon_refined.txt", 'w', encoding='utf-8')
lines = rfile.readlines()
lines = [l.strip() for l in lines if l.strip()]

print("lines: %d" %len(lines))

refinedLines = []
id = 1
item_cnt = 0
is_sequent_line = False
for e, l in enumerate(lines):
    if l == "대전":
        continue
    if id == 1:
        wfile.write('\nItem #\n')
        item_cnt += 1
    l = l.replace('\t\t', '\t').replace('\t\t', '\t').replace('\t\t', '\t').replace('\t', ', ').replace(', \n', '\n') ### dirty way of doing job
    if is_sequent_line is False:
        lineHeader = prefix[id-1]+":\t"
    else:
        lineHeader = ''
    if e < len(lines)-1 and id == 5 and lines[e+1].strip()[:6].replace('.', '').replace('(', '').isnumeric(): ### 현재 노출일시 행만 숫자(날짜 월)로 시작한다.
        is_sequent_line = True
        ends = ', '
    else:
        is_sequent_line = False
        ends = '\n'
        id += 1
    wfile.write(f'{lineHeader}{l}{ends}')
    if e < len(lines)-1 and id == 7 and lines[e+1].endswith("확진자"):
        continue
    else:
        if id > 6:
            id = 1

print("item count: %d" %item_cnt)