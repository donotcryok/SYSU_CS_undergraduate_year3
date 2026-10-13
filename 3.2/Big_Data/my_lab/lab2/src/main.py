import re
from py2neo import Graph, Node, Relationship

# 1. 数据库连接
graph = Graph("bolt://localhost:7687", auth=("neo4j", "12345678"))
graph.delete_all()

def professional_parser(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    #使用正则提取各个区块
    org_data = re.findall(r"ORG: (.*)", content)
    hero_data = re.findall(r"HERO: (.*)", content)
    rel_data = re.findall(r"REL: (.*)", content)

    #第一步：创建组织
    org_nodes = {}
    for org_name in org_data:
        node = Node("Organization", name=org_name.strip())
        graph.merge(node, "Organization", "name")
        org_nodes[org_name.strip()] = node

    #第二步：创建英雄并关联组织
    hero_nodes = {}
    for item in hero_data:
        #拆分: 英雄 | 真名 | 组织
        parts = [p.strip() for p in item.split("|")]
        if len(parts) == 3:
            h_name, r_name, aff_orgs = parts
            h_node = Node("Hero", name=h_name, real_name=r_name)
            graph.merge(h_node, "Hero", "name")
            hero_nodes[h_name] = h_node
            
            # 建立 MEMBER_OF 关系
            for o_name in aff_orgs.split(","):
                o_name = o_name.strip()
                if o_name in org_nodes:
                    graph.create(Relationship(h_node, "MEMBER_OF", org_nodes[o_name]))

    #第三步：创建人物关系
    for item in rel_data:
        #拆分: 起点 -> 关系 -> 终点
        parts = [p.strip() for p in item.split("->")]
        if len(parts) == 3:
            start_n, rel_type, end_n = parts
            
            #动态获取节点 (如果不存在则创建)
            n1 = hero_nodes.get(start_n) or Node("Hero", name=start_n)
            n2 = hero_nodes.get(end_n) or Node("Hero", name=end_n)
            graph.merge(n1, "Hero", "name")
            graph.merge(n2, "Hero", "name")
            
            graph.create(Relationship(n1, rel_type, n2))

    print("图谱构建成功！")

if __name__ == "__main__":
    professional_parser(r"E:\3.2\Big_Data\my_lab\lab2\src\MCU.txt")