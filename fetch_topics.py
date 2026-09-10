# -*- coding: utf-8 -*-
"""批量拉取各仓库「选题说明.md」并汇总"""
import json, urllib.request, urllib.parse, os, sys, time

# (姓名, owner/repo)
REPOS = [
    ("王煜淇", "hanyin-png/Vibecodingproject"),
    ("陈树涵", "1164448/tool-wear-prediction"),
    ("康浩然", "15845679403/khr"),
    ("屠意茁", "TUYIZHUO/predictive-maintenance-system"),
    ("虞恩溢", "yuenyi0511/hub"),
    ("鹿成富", "LU-RBG/eq_warn_system"),
    ("耿子昂", "19843753827/course-design-ai-project"),
    ("张徐诚", "zxc123916/dxbwork"),
    ("林柏旭", "LBX-d/object"),
    ("李志彭", "Baird-Li/Lizhipeng1"),
    ("朱行磊", "zxl258079/curriculum-design-project"),
    ("张小凡", "ZXF-deep/Vibecodingproject"),
    ("李汶阳", "Liwenyang111/liwenyang11"),
    ("谢兰宇", "198405373/course-design"),
    ("尚国龙", "longbao1001/Vibecodingproject"),
    ("罗志勇", "2026Lzy/Luo"),
    ("李佳焱", "lijiayan-vsg/ljy"),
    ("徐海烽", "xu123-hai/-"),
    ("杨京达", "yj0126-2006/yang"),
    ("李旺", "Li12389/li"),
    ("李勇琦", "lyq591/lyq2"),
    ("牛铭辰", "chunzhenmian/nmc14"),
    ("李骏", "Ljxhzswx159/desktop-tutorial"),
    ("王祎", "wangyi051029/biji"),
    ("孙宇涵", "luxuniii/course-design_ai"),
    ("杨松奇", "YuLin404NOTFOND/yulin"),
    ("董健", "dongjian666/dxbwork"),
    ("张孝通", "2670242589zero-star/manufacturing-intelligence-course-design"),
    ("郑煜昊", "zyh-27/zyhwork"),
    ("史竣琦", "sjq132/sjqde1"),
    ("高月明", "xingxi12/xingxi-notes"),
    ("荣展鹏", "RZP-RZP/rzp1"),
    ("李泳泽", "xiaozhou999100/xiaozhou"),
    ("沈东阳", "SDY12326/course-design-ai"),
    ("曹宇臣", "CYCCCC119/caoyuchen111.md"),
    ("范东巽", "fdx679/FDX1"),
    ("张昊", "uygby/zh111"),
    ("梁子健", "lzj531125/lzj7084951"),
    ("张芮源", "sakura-2-a/zry-ck"),
    ("邹明吾", "ZMW917/manufacture-intelligent-course-design"),
    ("刘家豪", "LJH-hub-max/ljh"),
    ("扎西", "zhaxi24/zxwk"),
    ("李禹泽", "yuze20060120/liyuze0120"),
    ("高尚", "gaoshang6668/ghwork"),
    ("齐欣", "733-qx/task"),
    ("杜佳瑄", "dujiaxuan02/an"),
    ("杨子询", "yangzixun222/course-design-graduation"),
    ("孙金雨", "sun20241202/git"),
    ("姜惠馨", "jhx-20241202/jhx"),
    ("潘泓旭", "phx123-dev/course-design"),
    ("董姝含", "dongdong1230-afk/Vibecodingproject"),
    ("罗志航", "luozhihang-lap/-"),
    ("白央", "By-040722/iot-work"),
    ("旦增拉布", "LBB-CYMK/LB"),
    ("张影", "zyy1126jy/parts-defect-inspection-system"),
    ("次仁旺加", "CRWJ-WJ/crwj"),
    ("王海阔", "qlbl6666/manufacturing-intelligent-course-design"),
    ("孙颢", "sunhao-lap/dxb"),
    ("荆昱升", "jys642/jys"),
    ("徐浩", "XU82670/topic-selection"),
    ("孙士凯", "sunshikai060101/manufacturing-intelligence-course"),
]

OUT_DIR = r"f:\ZMW\findings\topics"
os.makedirs(OUT_DIR, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 topic-fetcher"}

def http_get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()

def raw_get(owner, repo, branch, path):
    """path 不含前导斜杠；返回文本或 None"""
    q = urllib.parse.quote(path, safe="/")
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{q}"
    try:
        st, data = http_get(url)
        if st == 200:
            return data.decode("utf-8", "ignore")
    except Exception:
        pass
    return None

def api_tree(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
    try:
        st, data = http_get(url)
        if st == 200:
            return json.loads(data.decode("utf-8", "ignore"))
    except Exception:
        pass
    return None

def find_topic_path(tree_json):
    """在 tree 中找含「选题说明」或「选题」的 .md/.txt 文件路径"""
    if not tree_json or "tree" not in tree_json:
        return None
    candidates = []
    for item in tree_json["tree"]:
        p = item.get("path", "")
        base = os.path.basename(p).lower()
        if item.get("type") != "blob":
            continue
        if "选题说明" in p:
            candidates.append((0, p))
        elif "选题" in p and (base.endswith(".md") or base.endswith(".txt")):
            candidates.append((1, p))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]

def extract_fields(text):
    """从选题说明中粗略提取题目/目标/技术方向"""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    title = ""
    for l in lines:
        for kw in ("题目", "课题", "标题", "项目名称", "项目名"):
            if l.startswith(kw) or l.startswith("#") or l.startswith("##"):
                if kw in l and not title:
                    title = l
                    break
        if title:
            break
    return title

results = []
for i, (name, repo) in enumerate(REPOS, 1):
    owner, reponame = repo.split("/", 1)
    entry = {"no": i, "name": name, "repo": repo, "owner": owner, "status": "?", "path": None, "text": None, "title": ""}
    text = None
    path_used = None

    # 1) raw 猜测 root
    for branch in ("main", "master"):
        for fn in ("选题说明.md", "选题说明.MD", "选题说明.txt"):
            t = raw_get(owner, reponame, branch, fn)
            if t:
                text, path_used = t, fn
                break
        if text:
            break

    # 2) 回退 API tree
    if not text:
        tr = api_tree(owner, reponame)
        if tr:
            p = find_topic_path(tr)
            if p:
                for branch in ("main", "master"):
                    t = raw_get(owner, reponame, branch, p)
                    if t:
                        text, path_used = t, p
                        break

    if text:
        entry["status"] = "ok"
        entry["path"] = path_used
        entry["text"] = text
        entry["title"] = extract_fields(text)
        # 保存文件
        safe_name = f"{i:02d}_{name}"
        fp = os.path.join(OUT_DIR, safe_name + ".md")
        with open(fp, "w", encoding="utf-8") as f:
            f.write(f"<!-- repo: {repo} | path: {path_used} -->\n")
            f.write(text)
        print(f"[{i:02d}] {name}  OK  ({path_used}, {len(text)}字)")
    else:
        # 进一步：尝试 API 判断仓库是否存在（区分 notfound / 空 / 无文件）
        tr = api_tree(owner, reponame) if entry["status"] == "?" else None
        if tr is None:
            entry["status"] = "repo_notfound_or_error"
        elif tr.get("tree"):
            # 仓库存在但无选题说明文件，尝试 README
            readme = None
            for item in tr["tree"]:
                if item.get("type") == "blob" and item["path"].lower() == "readme.md":
                    readme = item["path"]; break
            if readme:
                for branch in ("main", "master"):
                    t = raw_get(owner, reponame, branch, readme)
                    if t:
                        entry["status"] = "no_topic_has_readme"
                        entry["text"] = t
                        entry["path"] = readme
                        fp = os.path.join(OUT_DIR, f"{i:02d}_{name}_README.md")
                        with open(fp, "w", encoding="utf-8") as f:
                            f.write(f"<!-- repo: {repo} | README 代替 -->\n" + t)
                        break
                if entry["status"] == "?":  # still unknown
                    entry["status"] = "no_topic_file"
            else:
                entry["status"] = "no_topic_file"
            print(f"[{i:02d}] {name}  {entry['status']}")
        else:
            entry["status"] = "empty_repo"
            print(f"[{i:02d}] {name}  empty_repo")
        entry["text"] = entry.get("text")

    results.append(entry)
    time.sleep(0.1)

# 输出汇总 JSON
with open(r"f:\ZMW\findings\fetch_results.json", "w", encoding="utf-8") as f:
    json.dump([{k: r[k] for k in ("no", "name", "repo", "status", "path", "title")} for r in results],
              f, ensure_ascii=False, indent=2)

# 控制台统计
from collections import Counter
c = Counter(r["status"] for r in results)
print("\n===== 统计 =====")
for k, v in c.items():
    print(f"  {k}: {v}")
print("total:", len(results))
