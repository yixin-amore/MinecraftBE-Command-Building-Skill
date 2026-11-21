#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Style profiles distilled from local architecture references."""
from dataclasses import dataclass, field
from typing import Dict, Tuple

@dataclass(frozen=True)
class StyleProfile:
    name: str
    verticality: Tuple[float,float]   # height / max(width,depth)
    bay_width: Tuple[int,int]
    buttress_every: Tuple[int,int]
    pinnacle_spacing: Tuple[int,int]
    courtyard_ratio: Tuple[float,float]  # 0 if no courtyard
    roof: str
    palette_roles: Dict[str,str] = field(default_factory=dict)

GOTHIC_KIRK = StyleProfile(
    'gothic-kirk',
    verticality=(1.15,2.80), bay_width=(5,9), buttress_every=(5,8),
    pinnacle_spacing=(3,6), courtyard_ratio=(0.0,0.0), roof='steep slate / dark copper',
    palette_roles={'base':'polished_deepslate / tuff','wall':'polished_andesite / stone',
                   'trim':'dark oak / deepslate','glass':'stained glass','roof':'deepslate_tiles'},
)
COURTYARD_CASTLE = StyleProfile(
    'courtyard-castle',
    verticality=(0.55,1.00), bay_width=(5,10), buttress_every=(6,12),
    pinnacle_spacing=(4,8), courtyard_ratio=(0.20,0.55), roof='steep gable + hip + one dominant spire',
    palette_roles={'base':'deepslate / cobble','wall':'stone bricks / calcite',
                   'trim':'polished deepslate','glass':'blue/purple stained','roof':'deepslate tiles / copper'},
)
STYLES={'gothic-kirk':GOTHIC_KIRK,'courtyard-castle':COURTYARD_CASTLE}

# Typology cards: coarse, keyword-searchable constraints from references/33.
ARCHETYPES = {
    'japanese-castle': {
        'keywords': ['姬路', '天守', '日式城堡', '白鹭', '石垣'],
        'site': '台地/石垣 + 外壕，逐层抬高',
        'sequence': '折返参道 → 城门 → 本丸',
        'section': '天守逐层收分，多重檐',
        'structure': '木构 + 倾斜石垣，白灰墙',
        'roof': '深瓦多重檐',
        'must': ['参道≥2次折返', '石垣斜坡', '真假箭窗', '逐层收分'],
    },
    'japanese-water-pavilion': {
        'keywords': ['金阁', '池', '倒影', '临水'],
        'site': '池岸，低视点',
        'sequence': '岸边步道 → 对岸借景',
        'section': '三层风格叠加',
        'structure': '木构，底层素木/上层金箔',
        'roof': '深瓦 + 凤凰饰',
        'must': ['水面≥35%', '底标高近水', '对岸主视点'],
    },
    'japanese-cliff-stage': {
        'keywords': ['清水寺', '悬空', '悬崖', '舞台'],
        'site': '悬崖/等高线',
        'sequence': '山门 → 本堂 → 悬空舞台',
        'section': '悬挑≥进深1/3，下方架空',
        'structure': '榉木立柱/榫卯/无钉',
        'roof': '深瓦，舞台无墙',
        'must': ['悬挑', '立柱分层', '架空腔'],
    },
    'korean-palace': {
        'keywords': ['景福宫', '韩式宫殿', '丹青', '月台', '勤政殿'],
        'site': '南北中轴，前朝后寝',
        'sequence': '光化门 → 勤政门 → 勤政殿',
        'section': '月台抬高，重檐歇山',
        'structure': '抬梁式，斗拱简化，露明梁架',
        'roof': '青灰瓦重檐歇山',
        'must': ['中轴对称', '月台2层', '丹青檐下', '青瓦'],
    },
    'korean-temple': {
        'keywords': ['佛国寺', '石台', '双塔', '廊庑'],
        'site': '山地台地',
        'sequence': '山门 → 大雄殿 → 极乐殿',
        'section': '双层石台，双塔并立',
        'structure': '花岗岩干砌台基 + 木殿',
        'roof': '歇山/悬山',
        'must': ['双层石台', '双塔一简一繁', '廊庑围合'],
    },
    'chinese-tang': {
        'keywords': ['佛光寺', '南禅寺', '唐构', '斗拱', '材份'],
        'site': '寺院高台/山村',
        'sequence': '山门 → 庭院 → 大殿',
        'section': '金厢斗底槽/三间四椽',
        'structure': '材份制，七铺作/五铺作',
        'roof': '庑殿/歇山，举折平缓',
        'must': ['斗拱雄大', '出檐≥3格', '屋顶平缓', '模数'],
    },
    'chinese-tower': {
        'keywords': ['应县木塔', '木塔', '套筒', '暗层'],
        'site': '城中心/寺院',
        'sequence': '塔基 → 明层 → 暗层',
        'section': '双层套筒，明五暗四',
        'structure': '叉柱造，逐层收分',
        'roof': '多层檐',
        'must': ['双筒', '明五暗四', '收分', '多种斗拱'],
    },
    'greek-classical': {
        'keywords': ['帕特农', '希腊', '多立克', '黄金比'],
        'site': '卫城高地',
        'sequence': '山门 → 前廊 → 内殿',
        'section': '围柱式',
        'structure': '多立克柱式，无柱础',
        'roof': '低坡山花',
        'must': ['4:9长宽', '9:4柱高柱径', '视差修正', '角柱加粗'],
    },
    'roman-dome': {
        'keywords': ['万神庙', '罗马', '穹顶', 'oculus'],
        'site': '城市广场',
        'sequence': '门廊 → 圆厅',
        'section': '单圆空间 + 穹顶',
        'structure': '分级骨料混凝土，厚墙',
        'roof': '穹顶 + 中央圆洞',
        'must': ['穹顶直径=高度', '凹格', '顶部圆洞', '厚墙'],
    },
    'gothic-cathedral': {
        'keywords': ['哥特', '飞扶壁', '玫瑰窗', '尖拱', '肋拱'],
        'site': '城市中心',
        'sequence': '西立面三门 → 中厅 → 唱诗班',
        'section': '高宽比≥2.5:1',
        'structure': '尖拱 + 肋拱 + 飞扶壁',
        'roof': '陡坡 + 尖塔',
        'must': ['飞扶壁', '玫瑰窗', '深窗', '垂直'],
    },
    'medieval-fortress': {
        'keywords': ['卡尔卡松', '要塞', '双墙', '瓮城', '城堡'],
        'site': '山脊/边境',
        'sequence': '外堡 → 双墙 → 城内',
        'section': '双重城墙 + 塔网',
        'structure': '石墙 + 瓮城',
        'roof': '塔楼/雉堞',
        'must': ['双重墙', '塔距≤2塔径', '瓮城', '曲折街巷'],
    },
    'estate-axis': {
        'keywords': ['凡尔赛', '庄园', '中轴', '镜厅', '几何园'],
        'site': '平原/河谷',
        'sequence': '前庭 → 镜厅 → 园林 → 运河',
        'section': '三段式立面',
        'structure': '石/砖 + 木屋架',
        'roof': '法式陡屋顶/老虎窗',
        'must': ['中轴', '镜面', '几何修剪', '水景递进'],
    },
}

def find_typology(text):
    """Rank typology cards by keyword hits."""
    out=[]
    for name,card in ARCHETYPES.items():
        score=sum(1 for k in card['keywords'] if k in text)
        if score: out.append((score,name))
    return [{'score':s,'type':n} for s,n in sorted(out,reverse=True)]



def check(style: StyleProfile, verticality: float, bay_width: int, buttress_every: int,
          pinnacle_spacing: int, courtyard_ratio: float=0.0):
    issues=[]
    def rng(label,v,lo,hi):
        if not (lo<=v<=hi): issues.append(f'{label} {v} outside [{lo},{hi}]')
    rng('verticality',verticality,*style.verticality)
    rng('bay_width',bay_width,*style.bay_width)
    rng('buttress_every',buttress_every,*style.buttress_every)
    rng('pinnacle_spacing',pinnacle_spacing,*style.pinnacle_spacing)
    rng('courtyard_ratio',courtyard_ratio,*style.courtyard_ratio)
    return {'style':style.name,'issues':issues,'ok':not issues}

if __name__=='__main__':
    print(check(GOTHIC_KIRK,1.27,7,6,4,0.0))
    print(find_typology('姬路城 天守 石垣 白鹭'))
    print(check(COURTYARD_CASTLE,0.73,8,8,6,0.30))
