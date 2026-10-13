# -*- coding: utf-8 -*-
"""
Web演示界面
基于Flask的足球球员推荐系统演示
"""

import pandas as pd
import numpy as np
from flask import Flask, render_template_string, request, jsonify
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data_preprocessing import DataPreprocessor
from hybrid_recommender import HybridRecommender

app = Flask(__name__)

preprocessor = None
hybrid_model = None

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>足球球员智能推荐系统</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #1a5276 0%, #2ecc71 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .card h2 {
            color: #1a5276;
            margin-bottom: 15px;
            font-size: 1.4em;
            border-bottom: 3px solid #2ecc71;
            padding-bottom: 10px;
        }
        .form-group { margin-bottom: 15px; }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: bold;
        }
        select, input {
            width: 100%;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
        }
        select:focus, input:focus {
            border-color: #2ecc71;
            outline: none;
        }
        .btn {
            background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            font-size: 16px;
            border-radius: 8px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .btn:hover { transform: translateY(-2px); }
        .btn-analyze {
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            margin-right: 10px;
        }
        .recommendations {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .rec-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 10px;
            padding: 15px;
            border-left: 4px solid #2ecc71;
        }
        .rec-card h3 { color: #1a5276; margin-bottom: 8px; font-size: 1.1em; }
        .rec-card .score { color: #2ecc71; font-weight: bold; }
        .rec-card .explanation { color: #666; font-size: 0.85em; margin-top: 8px; font-style: italic; }
        .player-info { color: #555; margin: 3px 0; font-size: 0.9em; }
        
        /* 球队需求分析样式 */
        .needs-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-bottom: 15px;
        }
        .need-card {
            padding: 12px;
            border-radius: 8px;
            text-align: center;
        }
        .need-card.sufficient { background: #d4edda; border: 1px solid #28a745; }
        .need-card.needed { background: #fff3cd; border: 1px solid #ffc107; }
        .need-card.urgent { background: #f8d7da; border: 1px solid #dc3545; }
        .need-card .position-name { font-weight: bold; font-size: 1.1em; margin-bottom: 5px; }
        .need-card .count { font-size: 1.5em; font-weight: bold; }
        .need-card .status { font-size: 0.8em; margin-top: 5px; }
        
        .age-analysis {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        .age-bars {
            display: flex;
            height: 30px;
            border-radius: 5px;
            overflow: hidden;
            margin-top: 10px;
        }
        .age-bar {
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 0.8em;
            font-weight: bold;
        }
        .age-bar.young { background: #28a745; }
        .age-bar.prime { background: #007bff; }
        .age-bar.veteran { background: #6c757d; }
        
        .player-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            font-size: 0.9em;
        }
        .player-table th {
            background: #1a5276;
            color: white;
            padding: 10px;
            text-align: left;
        }
        .player-table td {
            padding: 8px 10px;
            border-bottom: 1px solid #eee;
        }
        .player-table tr:hover { background: #f5f5f5; }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-item {
            background: linear-gradient(135deg, #1a5276 0%, #2ecc71 100%);
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-item .number { font-size: 1.8em; font-weight: bold; }
        .stat-item .label { font-size: 0.85em; opacity: 0.9; }
        .loading { display: none; text-align: center; padding: 15px; color: #2ecc71; }
        
        .algorithm-desc {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-top: 10px;
        }
        .algorithm-desc p { margin-bottom: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>足球球员智能推荐系统</h1>
        
        <div class="card">
            <div class="stats" id="stats">
                <div class="stat-item">
                    <div class="number" id="player-count">-</div>
                    <div class="label">球员数量</div>
                </div>
                <div class="stat-item">
                    <div class="number" id="club-count">-</div>
                    <div class="label">俱乐部数量</div>
                </div>
                <div class="stat-item">
                    <div class="number" id="transfer-count">-</div>
                    <div class="label">转会记录</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>球员推荐</h2>
            
            <div style="display: flex; gap: 15px; align-items: end;">
                <div class="form-group" style="flex: 1;">
                    <label for="rec-type">推荐类型：</label>
                    <select id="rec-type" onchange="toggleRecType()">
                        <option value="club">为俱乐部推荐球员</option>
                        <option value="similar">推荐相似球员</option>
                    </select>
                </div>
                
                <div id="club-section" class="form-group" style="flex: 2;">
                    <label for="club-select">选择俱乐部：</label>
                    <select id="club-select">
                        <option value="">-- 请选择俱乐部 --</option>
                    </select>
                </div>
                
                <div id="player-section" class="form-group" style="flex: 2; display:none;">
                    <label for="player-select">选择球员：</label>
                    <select id="player-select">
                        <option value="">-- 请选择球员 --</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <button class="btn btn-analyze" onclick="analyzeTeam()">分析需求</button>
                    <button class="btn" onclick="getRecommendations()">获取推荐</button>
                </div>
            </div>
            
            <div style="display: flex; gap: 15px;">
                <div class="form-group" style="flex: 1;">
                    <label for="position-filter">位置过滤：</label>
                    <select id="position-filter">
                        <option value="">全部位置</option>
                        <option value="Goalkeeper">守门员</option>
                        <option value="Defender">后卫</option>
                        <option value="Midfielder">中场</option>
                        <option value="Forward">前锋</option>
                    </select>
                </div>
                <div class="form-group" style="flex: 1;">
                    <label for="rec-count">推荐数量：</label>
                    <input type="number" id="rec-count" value="10" min="1" max="20">
                </div>
            </div>
            
            <div class="loading" id="loading">正在处理，请稍候...</div>
        </div>
        
        <!-- 球队需求分析区域 -->
        <div class="card" id="team-needs-card" style="display:none;">
            <h2>球队需求分析</h2>
            <div id="team-needs-content"></div>
        </div>
        
        <!-- 推荐结果区域 -->
        <div class="card" id="result-card" style="display:none;">
            <h2>推荐结果</h2>
            <div class="recommendations" id="recommendations"></div>
        </div>
        
        <div class="card">
            <h2>算法说明</h2>
            <div class="algorithm-desc">
                <p><strong>协同过滤</strong>：基于俱乐部历史引援行为，推荐相似俱乐部签入的球员</p>
                <p><strong>基于内容推荐</strong>：根据球员表现特征（进球、助攻、出场等）匹配推荐</p>
                <p><strong>位置需求感知</strong>：分析球队阵容缺口，优先推荐急需位置的球员</p>
                <p><strong>混合推荐</strong>：自适应融合多种推荐策略，综合考虑球队需求</p>
            </div>
        </div>
    </div>
    
    <script>
        window.onload = function() {
            fetch('/api/stats')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('player-count').textContent = data.n_players || 0;
                    document.getElementById('club-count').textContent = data.n_clubs || 0;
                    document.getElementById('transfer-count').textContent = data.n_transfers || 0;
                });
            
            fetch('/api/clubs')
                .then(r => r.json())
                .then(clubs => {
                    const select = document.getElementById('club-select');
                    clubs.forEach(club => {
                        const option = document.createElement('option');
                        option.value = club.id;
                        option.textContent = club.name;
                        select.appendChild(option);
                    });
                });
            
            fetch('/api/players')
                .then(r => r.json())
                .then(players => {
                    const select = document.getElementById('player-select');
                    players.forEach(p => {
                        const option = document.createElement('option');
                        option.value = p.id;
                        option.textContent = p.name + ' (' + p.position + ')';
                        select.appendChild(option);
                    });
                });
        }
        
        function toggleRecType() {
            const type = document.getElementById('rec-type').value;
            document.getElementById('club-section').style.display = type === 'club' ? 'block' : 'none';
            document.getElementById('player-section').style.display = type === 'similar' ? 'block' : 'none';
        }
        
        // 分析球队需求
        function analyzeTeam() {
            const clubId = document.getElementById('club-select').value;
            if (!clubId) { alert('请先选择俱乐部'); return; }
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('team-needs-card').style.display = 'none';
            
            fetch('/api/team_needs', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ club_id: parseInt(clubId) })
            })
            .then(r => r.json())
            .then(data => {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('team-needs-card').style.display = 'block';
                renderTeamNeeds(data);
            })
            .catch(err => {
                document.getElementById('loading').style.display = 'none';
                alert('分析失败: ' + err);
            });
        }
        
        // 渲染球队需求分析
        function renderTeamNeeds(data) {
            const container = document.getElementById('team-needs-content');
            let html = '';
            
            html += '<h3 style="margin-bottom:15px;">' + data.club_name + '</h3>';
            html += '<p style="margin-bottom:15px;">当前球员总数: <strong>' + data.total_players + '</strong></p>';
            
            // 位置需求分析
            html += '<h4 style="margin-bottom:10px;">位置需求分析</h4>';
            html += '<div class="needs-grid">';
            
            const positions = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward'];
            const posNames = {'Goalkeeper': '门将', 'Defender': '后卫', 'Midfielder': '中场', 'Forward': '前锋'};
            
            positions.forEach(pos => {
                const analysis = data.position_analysis[pos] || { current: 0, ideal: 0, gap: 0, status: 'sufficient' };
                const statusText = {'sufficient': '充足', 'needed': '需要', 'urgent': '紧急'};
                html += '<div class="need-card ' + analysis.status + '">';
                html += '<div class="position-name">' + posNames[pos] + '</div>';
                html += '<div class="count">' + analysis.current + ' / ' + analysis.ideal + '</div>';
                html += '<div class="status">' + statusText[analysis.status] + (analysis.gap > 0 ? ' (缺' + analysis.gap + '人)' : '') + '</div>';
                html += '</div>';
            });
            html += '</div>';
            
            // 年龄结构分析
            if (data.age_analysis) {
                const age = data.age_analysis;
                html += '<h4 style="margin-bottom:10px;">年龄结构分析</h4>';
                html += '<div class="age-analysis">';
                html += '<p>平均年龄: <strong>' + age.average_age + '</strong>岁 | ';
                html += '年轻球员比例: <strong>' + age.young_ratio + '%</strong> | ';
                html += '需要引进年轻球员: <strong>' + (age.needs_young ? '是' : '否') + '</strong></p>';
                
                const total = age.young_count + age.prime_count + age.veteran_count;
                if (total > 0) {
                    html += '<div class="age-bars">';
                    const youngWidth = (age.young_count / total * 100).toFixed(1);
                    const primeWidth = (age.prime_count / total * 100).toFixed(1);
                    const veteranWidth = (age.veteran_count / total * 100).toFixed(1);
                    html += '<div class="age-bar young" style="width:' + youngWidth + '%">U24: ' + age.young_count + '</div>';
                    html += '<div class="age-bar prime" style="width:' + primeWidth + '%">24-30: ' + age.prime_count + '</div>';
                    html += '<div class="age-bar veteran" style="width:' + veteranWidth + '%">30+: ' + age.veteran_count + '</div>';
                    html += '</div>';
                }
                html += '</div>';
            }
            
            // 当前球员列表
            if (data.player_list && data.player_list.length > 0) {
                html += '<h4 style="margin:15px 0 10px;">当前阵容</h4>';
                html += '<div style="max-height:400px; overflow-y:auto;">';
                html += '<table class="player-table">';
                html += '<tr><th>姓名</th><th>位置</th><th>年龄</th><th>身价</th></tr>';
                
                data.player_list.forEach(p => {
                    const value = p.market_value > 0 ? (p.market_value / 1000000).toFixed(1) + 'M' : '-';
                    html += '<tr><td>' + p.name + '</td><td>' + p.position + '</td><td>' + p.age + '</td><td>' + value + '</td></tr>';
                });
                
                html += '</table></div>';
            }
            
            container.innerHTML = html;
        }
        
        // 获取推荐
        function getRecommendations() {
            const type = document.getElementById('rec-type').value;
            const count = document.getElementById('rec-count').value;
            const position = document.getElementById('position-filter').value;
            
            let endpoint, body;
            
            if (type === 'club') {
                const clubId = document.getElementById('club-select').value;
                if (!clubId) { alert('请选择俱乐部'); return; }
                endpoint = '/api/recommend/club';
                body = { club_id: parseInt(clubId), n_items: parseInt(count), position: position || null };
            } else {
                const playerId = document.getElementById('player-select').value;
                if (!playerId) { alert('请选择球员'); return; }
                endpoint = '/api/recommend/similar';
                body = { player_id: parseInt(playerId), n_items: parseInt(count) };
            }
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('result-card').style.display = 'none';
            
            fetch(endpoint, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(body)
            })
            .then(r => r.json())
            .then(data => {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('result-card').style.display = 'block';
                
                const container = document.getElementById('recommendations');
                container.innerHTML = '';
                
                if (data.recommendations) {
                    data.recommendations.forEach(rec => {
                        const card = document.createElement('div');
                        card.className = 'rec-card';
                        const marketValue = rec.market_value ? (rec.market_value / 1000000).toFixed(1) + 'M' : '-';
                        card.innerHTML = '<h3>' + rec.name + '</h3>' +
                            '<p class="player-info">位置: ' + rec.position + ' | 年龄: ' + rec.age + '</p>' +
                            '<p class="player-info">身价: ' + marketValue + '</p>' +
                            '<p class="score">推荐分数: ' + rec.score.toFixed(3) + '</p>' +
                            '<p class="explanation">' + rec.explanation + '</p>';
                        container.appendChild(card);
                    });
                }
            })
            .catch(err => {
                document.getElementById('loading').style.display = 'none';
                alert('推荐失败: ' + err);
            });
        }
    </script>
</body>
</html>
'''

def init_model():
    """初始化模型"""
    global preprocessor, hybrid_model
    
    print("Initializing model...")
    preprocessor = DataPreprocessor(data_path='../data')
    preprocessor.load_data().clean_data().feature_engineering()
    
    hybrid_model = HybridRecommender()
    hybrid_model.fit(preprocessor.players_df, preprocessor.transfers_df)
    print("Model initialization completed!")


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/stats')
def get_stats():
    stats = preprocessor.get_statistics()
    return jsonify(stats)


@app.route('/api/clubs')
def get_clubs():
    """获取俱乐部列表"""
    clubs = []
    
    if preprocessor.clubs_df is not None and len(preprocessor.clubs_df) > 0:
        for _, row in preprocessor.clubs_df.iterrows():
            club_id = row.get('club_id')
            club_name = row.get('club_name', '')
            if pd.notna(club_id) and club_id:
                clubs.append({
                    'id': int(club_id),
                    'name': str(club_name) if club_name else f"Club_{int(club_id)}"
                })
    elif 'current_club_id' in preprocessor.players_df.columns:
        club_data = preprocessor.players_df[['current_club_id', 'current_club_name']].dropna()
        club_data = club_data.drop_duplicates(subset=['current_club_id'])
        club_data = club_data.head(100)
        for _, row in club_data.iterrows():
            clubs.append({
                'id': int(row['current_club_id']),
                'name': str(row.get('current_club_name', f"Club_{int(row['current_club_id'])}"))
            })
    
    clubs.sort(key=lambda x: x['name'])
    return jsonify(clubs)


@app.route('/api/players')
def get_players():
    """获取球员列表"""
    players = []
    
    if 'market_value' in preprocessor.players_df.columns:
        player_data = preprocessor.players_df.nlargest(200, 'market_value')
    else:
        player_data = preprocessor.players_df.head(200)
    
    for _, row in player_data.iterrows():
        player_id = row.get('player_id')
        player_name = row.get('player_name', '')
        position = row.get('main_position', row.get('position_category', '-'))
        
        if pd.notna(player_id):
            players.append({
                'id': int(player_id),
                'name': str(player_name) if player_name else f"Player_{int(player_id)}",
                'position': str(position) if position else '-'
            })
    
    return jsonify(players)


@app.route('/api/team_needs', methods=['POST'])
def team_needs():
    """获取球队需求分析"""
    data = request.json
    club_id = data.get('club_id')
    
    try:
        needs = hybrid_model.content_recommender.build_team_need_profile(club_id, preprocessor.players_df)
        
        if needs is None:
            return jsonify({'error': 'Club not found or has no players'}), 404
        
        return jsonify(needs)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/recommend/club', methods=['POST'])
def recommend_for_club():
    """为俱乐部推荐球员"""
    data = request.json
    club_id = data.get('club_id')
    n_items = data.get('n_items', 10)
    position = data.get('position')
    
    try:
        recommendations = hybrid_model.recommend_for_club(
            club_id, n_items=n_items, position_filter=position
        )
        
        results = []
        for player_id, score in recommendations:
            player = preprocessor.players_df[preprocessor.players_df['player_id'] == player_id]
            if len(player) > 0:
                p = player.iloc[0]
                explanation = hybrid_model.get_recommendation_explanation(player_id, club_id)
                
                name = str(p.get('player_name', f'Player_{player_id}')) if pd.notna(p.get('player_name')) else f'Player_{player_id}'
                position_val = str(p.get('main_position', p.get('position_category', '-'))) if pd.notna(p.get('main_position')) else '-'
                age = int(p.get('age', 0)) if pd.notna(p.get('age')) else 0
                market_value = float(p.get('market_value', 0)) if pd.notna(p.get('market_value')) else 0
                
                results.append({
                    'name': name,
                    'position': position_val,
                    'age': age,
                    'market_value': market_value,
                    'score': float(score),
                    'explanation': explanation
                })
        
        return jsonify({'recommendations': results})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400


@app.route('/api/recommend/similar', methods=['POST'])
def recommend_similar():
    """推荐相似球员"""
    data = request.json
    player_id = data.get('player_id')
    n_items = data.get('n_items', 10)
    
    try:
        recommendations = hybrid_model.recommend_similar_player(player_id, n_items=n_items)
        
        results = []
        for pid, score in recommendations:
            player = preprocessor.players_df[preprocessor.players_df['player_id'] == pid]
            if len(player) > 0:
                p = player.iloc[0]
                
                name = str(p.get('player_name', f'Player_{pid}')) if pd.notna(p.get('player_name')) else f'Player_{pid}'
                position_val = str(p.get('main_position', p.get('position_category', '-'))) if pd.notna(p.get('main_position')) else '-'
                age = int(p.get('age', 0)) if pd.notna(p.get('age')) else 0
                market_value = float(p.get('market_value', 0)) if pd.notna(p.get('market_value')) else 0
                
                results.append({
                    'name': name,
                    'position': position_val,
                    'age': age,
                    'market_value': market_value,
                    'score': float(score),
                    'explanation': '能力特征相似'
                })
        
        return jsonify({'recommendations': results})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400


def run_demo():
    """运行演示"""
    init_model()
    print("\n" + "="*50)
    print("Demo service starting...")
    print("Please visit: http://127.0.0.1:5000")
    print("="*50 + "\n")
    app.run(debug=False, port=5000)


if __name__ == '__main__':
    run_demo()
