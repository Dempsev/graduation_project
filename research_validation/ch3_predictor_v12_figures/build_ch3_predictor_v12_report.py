from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "research_validation" / "ch3_predictor_v12_figures"
DATA_DIR = ROOT / "data" / "prediction_targetband_param_v1" / "v1" / "windows_dense_v12_all_history_ga20_clean_v1"
READINESS_DIR = ROOT / "data" / "analysis" / "predictor_readiness_v12_all_history_ga20_clean_v1"
RUN_DIR = ROOT / "data" / "prediction_targetband_param_v1_runs"

THESIS_BANDS = ["band140_180", "band160_200", "band180_220", "band200_240", "band220_260", "band240_280"]
BAND_LABELS = {
    "band140_180": "140-180 Hz",
    "band160_200": "160-200 Hz",
    "band180_220": "180-220 Hz",
    "band200_240": "200-240 Hz",
    "band220_260": "220-260 Hz",
    "band240_280": "240-280 Hz",
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def csv_row_count(path: Path) -> int:
    return len(pd.read_csv(path, low_memory=False))


def fmt(value: float, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}"


def md_table(headers: list[str], rows: list[list[object]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(out)


def tsv_table(title: str, headers: list[str], rows: list[list[object]]) -> str:
    out = [title, "\t".join(headers)]
    out.extend("\t".join(str(item) for item in row) for row in rows)
    return "\n".join(out)


def build_file_inventory(info: dict) -> list[list[object]]:
    entries = [
        ("targetband_parametric_v1.csv", "3.2 样本数据库构建；3.3 模型训练样本", "清洗后的 v12 条件预测训练数据集"),
        ("dataset_info.json", "3.2 数据来源与统计；图 3-1/3-2", "数据规模、来源、清洗规则、频带统计"),
        ("stacked_before_cleaning_v1.csv", "3.2 数据预处理", "清洗前历史数据和 GA 数据堆叠记录"),
        ("ga20_active_band_added_rows_v1.csv", "3.2 数据来源；3.5 高频段讨论", "20 代 COMSOL 闭环 GA 的 active-band 真值"),
        ("data_conflicts_resolved_v1.csv", "3.2 冲突处理", "标签冲突样本审计记录"),
        ("source_counts_v1.csv", "3.2 数据来源组成", "各历史数据源堆叠行数"),
    ]
    rows: list[list[object]] = []
    for name, section, note in entries:
        path = DATA_DIR / name
        exists = path.exists()
        if path.suffix == ".csv" and exists:
            content = f"{csv_row_count(path):,} 行"
        elif exists:
            content = (
                f"清洗后 {info['rows_clean_after_physical_key_dedup']:,} 行；"
                f"冲突物理键 {info['conflict_physical_keys']} 个；"
                f"GA20 有效源记录 {info['rows_ga20_valid_source']} 条"
            )
        else:
            content = "【待确认】文件缺失"
        rows.append([rel(path), "是" if exists else "否", content, section, note])
    return rows


def build_field_rows(columns: set[str], raw_ga_columns: set[str]) -> list[list[object]]:
    rows = [
        ["physical_key", "是", "由 point_id、shape_id、结构参数和目标频带上下限构成的物理去重键。", "最终训练集、冲突表"],
        ["point_id", "是", "结构参数采样点或设计点编号。", "最终训练集、GA 历史"],
        ["shape_id", "是", "形状轮廓或结构形状编号。", "最终训练集、GA 历史"],
        ["shape_family", "是", "形状族类别字段；未发现独立 `family` 字段。", "最终训练集"],
        ["target_band_low_Hz", "是", "目标频带下限。", "最终训练集"],
        ["target_band_high_Hz", "是", "目标频带上限。", "最终训练集"],
        ["target_band_center_Hz", "是", "目标频带中心频率。", "最终训练集"],
        ["target_band_width_Hz", "是", "目标频带宽度。", "最终训练集"],
        ["target_gap_is_open", "是", "分类标签，表示目标频带内是否存在正重叠带隙。", "分类器训练标签"],
        ["target_gap_cover_ratio", "是", "回归主标签，表示目标频带覆盖率。", "回归器训练标签"],
        ["target_gap_overlap_Hz", "是", "真实 overlap 字段；`target_overlap_Hz` 未发现。", "用于解释覆盖率来源"],
        ["geometry_valid", "否/上游有", "最终训练集未保留；原始 GA 历史 `ga_history_v1.csv` 中存在。", "GA 有效性筛选证据"],
        ["contact_valid", "否/上游有", "最终训练集未保留；原始 GA 历史 `ga_history_v1.csv` 中存在。", "GA 有效性筛选证据"],
        ["solve_success", "否/上游有", "最终训练集未保留；原始 GA 历史 `ga_history_v1.csv` 中存在。", "COMSOL 求解成功筛选证据"],
        [
            "source/provenance",
            "是",
            "真实字段包括 source_dataset_version、source_record_kind、source_priority、source_dataset_versions、source_record_kinds、source_param_sample_ids、source_stage、active_learning_source_ga_history、ga20_candidate_id、data_cleaning_conflict_flag。",
            "数据来源追踪与冲突审计",
        ],
    ]
    return rows


def dataset_tables(info: dict) -> dict[str, list[list[object]]]:
    construct = [
        ["历史数据堆叠行数", f"{info['rows_historical_stacked']:,}", "历史目标频带、补充真值和主动学习版本的堆叠记录"],
        ["20 代 GA 有效 COMSOL 源记录", f"{info['rows_ga20_valid_source']:,}", "通过 geometry/contact/solve 筛选后的 active-band 记录"],
        ["20 代 GA 追加 active-band 记录", f"{info['rows_ga20_added_active_band_only']:,}", "仅追加真实优化频带，不做跨频带扩展"],
        ["清洗前总行数", f"{info['rows_stacked_before_cleaning']:,}", "历史数据与 GA20 active-band 数据合并后"],
        ["按 physical_key 去重后总行数", f"{info['rows_clean_after_physical_key_dedup']:,}", "第三章模型训练使用的数据集规模"],
        ["重复物理键数量", f"{info['duplicate_physical_keys']:,}", "重复样本审计结果"],
        ["标签冲突物理键", f"{info['conflict_physical_keys']:,}", "已按 origin-target 一致性和来源优先级处理"],
        ["唯一结构设计数", f"{info['unique_designs']:,}", "清洗后 design_id 数量"],
        ["唯一形状数", f"{info['unique_shapes']:,}", "清洗后 shape_id 数量"],
        ["唯一形状族数", f"{info['unique_families']:,}", "清洗后 shape_family 数量"],
    ]
    band_rows = []
    for item in info["thesis_band_summary"]:
        band_rows.append(
            [
                BAND_LABELS[item["target_band_tag"]],
                f"{item['rows']:,}",
                f"{item['positive_rows']:,}",
                fmt(item["positive_rate"]),
                fmt(item["max_cover_ratio"]),
                fmt(item["mean_cover_ratio"]),
            ]
        )
    return {"construct": construct, "bands": band_rows}


def model_tables(readiness: dict) -> dict[str, list[list[object]]]:
    feature_rows = [
        ["结构参数", "a1, a2, b1, b2, a3, b3, a4, b4, a5, b5, r0", "描述结构轮廓和几何参数化形式", "数值化后直接输入模型"],
        ["结构族字段", "shape_id, shape_family", "表示结构形状编号和结构族类别", "用于分组验证和结构族感知分析"],
        ["形状统计特征", "shape_area, shape_perimeter, shape_compactness, shape_solidity 等", "描述结构轮廓面积、周长、紧致度、凸性等", "作为数值特征输入"],
        ["目标频带条件", "target_band_low_Hz, target_band_high_Hz, target_band_center_Hz, target_band_width_Hz", "定义条件预测中的目标频带 B", "作为条件变量拼接到输入特征"],
        ["来源与审计字段", "source_dataset_version, source_record_kind, physical_key", "用于数据追踪、去重和冲突审计", "不作为物理输出标签"],
    ]
    stage_rows = [
        ["HGB Classifier", "判断目标频带内是否存在带隙重叠", "46,754", "target_gap_is_open / p_open", "用于候选初筛"],
        ["HGB Regressor", "在正样本上预测目标频带覆盖率", "30,716", "target_gap_cover_ratio / c_hat", "用于候选排序"],
    ]
    overall_rows = [
        [
            "形状族分组 5 折",
            fmt(readiness["family_cv"]["classifier"]["accuracy"]),
            fmt(readiness["family_cv"]["classifier"]["f1"]),
            fmt(readiness["family_cv"]["classifier"]["balanced_accuracy"]),
            fmt(readiness["family_cv"]["regressor_overall"]["mae"], 4),
            fmt(readiness["family_cv"]["regressor_overall"]["rmse"], 4),
            fmt(readiness["family_cv"]["regressor_overall"]["r2"]),
        ],
        [
            "留一频带",
            fmt(readiness["leave_one_band"]["classifier"]["accuracy"]),
            fmt(readiness["leave_one_band"]["classifier"]["f1"]),
            fmt(readiness["leave_one_band"]["classifier"]["balanced_accuracy"]),
            fmt(readiness["leave_one_band"]["regressor_overall"]["mae"], 4),
            fmt(readiness["leave_one_band"]["regressor_overall"]["rmse"], 4),
            fmt(readiness["leave_one_band"]["regressor_overall"]["r2"]),
        ],
    ]
    family_cls = pd.read_csv(READINESS_DIR / "family_cv_classifier_by_band.csv").set_index("target_band_tag").loc[THESIS_BANDS]
    lobo_cls = pd.read_csv(READINESS_DIR / "leave_one_band_classifier_by_band.csv").set_index("target_band_tag").loc[THESIS_BANDS]
    cls_rows = []
    for tag in THESIS_BANDS:
        cls_rows.append(
            [
                BAND_LABELS[tag],
                fmt(family_cls.loc[tag, "f1"]),
                fmt(family_cls.loc[tag, "balanced_accuracy"]),
                fmt(lobo_cls.loc[tag, "f1"]),
                fmt(lobo_cls.loc[tag, "balanced_accuracy"]),
            ]
        )
    family_reg = pd.read_csv(READINESS_DIR / "family_cv_regressor_by_band.csv").set_index("target_band_tag").loc[THESIS_BANDS]
    lobo_reg = pd.read_csv(READINESS_DIR / "leave_one_band_regressor_by_band.csv").set_index("target_band_tag").loc[THESIS_BANDS]
    reg_rows = [[BAND_LABELS[tag], fmt(family_reg.loc[tag, "mae"], 4), fmt(lobo_reg.loc[tag, "mae"], 4)] for tag in THESIS_BANDS]
    family_topk = pd.read_csv(READINESS_DIR / "family_cv_topk_summary.csv").set_index("k")
    lobo_topk = pd.read_csv(READINESS_DIR / "leave_one_band_topk_summary.csv").set_index("k")
    topk_rows = [
        ["形状族分组 5 折", fmt(family_topk.loc[5, "mean_topk_hit_rate"]), fmt(family_topk.loc[5, "mean_topk_cover"]), fmt(family_topk.loc[10, "mean_topk_hit_rate"]), fmt(family_topk.loc[10, "mean_topk_cover"])],
        ["留一频带", fmt(lobo_topk.loc[5, "mean_topk_hit_rate"]), fmt(lobo_topk.loc[5, "mean_topk_cover"]), fmt(lobo_topk.loc[10, "mean_topk_hit_rate"]), fmt(lobo_topk.loc[10, "mean_topk_cover"])],
    ]
    return {
        "features": feature_rows,
        "stages": stage_rows,
        "overall": overall_rows,
        "classification": cls_rows,
        "regression": reg_rows,
        "topk": topk_rows,
    }


def build_report() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    info = load_json(DATA_DIR / "dataset_info.json")
    readiness = load_json(READINESS_DIR / "readiness_summary.json")
    target_cols = set(pd.read_csv(DATA_DIR / "targetband_parametric_v1.csv", nrows=1, low_memory=False).columns)
    raw_ga_path = ROOT / "data" / "comsol_batch" / "comsol_in_loop_thesis_band140_180_overlap_ga_v1" / "ga_history_v1.csv"
    raw_ga_cols = set(pd.read_csv(raw_ga_path, nrows=1, low_memory=False).columns)
    dsets = dataset_tables(info)
    mtables = model_tables(readiness)
    file_inventory = build_file_inventory(info)
    field_rows = build_field_rows(target_cols, raw_ga_cols)
    figure_index = pd.read_csv(OUT_DIR / "ch3_figure_index.csv")

    evidence_rows = [
        [rel(ROOT / "prediction_targetband_param_v1" / "tools" / "build_thesis_ga20_all_data_dataset_v12.py"), "数据集构建脚本", "合并历史数据与 20 代 GA active-band 真值，生成 v12 清洗数据集", "3.2", "已运行生成 v12"],
        [rel(ROOT / "prediction_targetband_param_v1" / "models" / "train_parametric_targetband_classifier_v1.py"), "训练脚本", "HGB 分类器交叉验证训练入口", "3.3/3.5", "本次未重训"],
        [rel(ROOT / "prediction_targetband_param_v1" / "models" / "train_parametric_targetband_regressor_v1.py"), "训练脚本", "HGB 覆盖率回归器交叉验证训练入口", "3.3/3.5", "本次未重训"],
        [rel(RUN_DIR / "param_targetband_final_hgb_dense_v12_all_history_ga20_clean_v1" / "final_predictor_bundle.joblib"), "模型包", "全量 v12 final predictor bundle", "3.3", "最终可调用模型"],
        [rel(RUN_DIR / "param_targetband_cls_hgb_dense_v12_all_history_ga20_clean_v1" / "stratified_group_kfold"), "分类器结果目录", "Family-CV 分类器 fold、预测和汇总结果", "3.5", "主验证依据之一"],
        [rel(RUN_DIR / "param_targetband_cover_hgb_dense_v12_all_history_ga20_clean_v1" / "stratified_group_kfold"), "回归器结果目录", "Family-CV 覆盖率回归 fold、预测和汇总结果", "3.5", "主验证依据之一"],
        [rel(READINESS_DIR), "readiness 汇总目录", "六个论文目标频带过滤后的指标、Top-k 排序能力结果", "3.5", "第三章主表优先用这里"],
        [rel(OUT_DIR / "build_ch3_predictor_v12_figures.py"), "绘图脚本", "生成 7 张第三章 ch3_ PNG/SVG 图", "3.2-3.5", "未重训模型"],
    ]

    figure_rows = [
        [rel(Path(row["png_path"])), rel(Path(row["svg_path"])), row["caption_suggestion"]]
        for _, row in figure_index.iterrows()
    ]

    word_tables = [
        tsv_table("1）v12 数据集构成表", ["项目", "数量", "说明"], dsets["construct"]),
        tsv_table("2）六个目标频带样本统计表", ["目标频带", "样本数", "正样本数", "正样本率", "最大覆盖率", "平均覆盖率"], dsets["bands"]),
        tsv_table("3）条件预测模型输入特征表", ["特征类别", "代表字段", "含义", "处理方式"], mtables["features"]),
        tsv_table("4）两阶段预测模型任务分工表", ["模型", "任务", "训练样本", "输出标签", "作用"], mtables["stages"]),
        tsv_table("5）模型总体验证结果表", ["验证方式", "分类准确率", "分类F1", "分类平衡准确率", "覆盖率MAE", "覆盖率RMSE", "覆盖率R²"], mtables["overall"]),
        tsv_table("6）六个目标频带分类结果表", ["目标频带", "Family-CV F1", "Family-CV平衡准确率", "Band-LOO F1", "Band-LOO平衡准确率"], mtables["classification"]),
        tsv_table("7）六个目标频带回归结果表", ["目标频带", "Family-CV MAE", "Band-LOO MAE"], mtables["regression"]),
        tsv_table("8）Top-k排序能力表", ["验证方式", "Top-5命中率", "Top-5平均真实覆盖率", "Top-10命中率", "Top-10平均真实覆盖率"], mtables["topk"]),
    ]
    (OUT_DIR / "ch3_word_tables.tsv.txt").write_text("\n\n".join(word_tables), encoding="utf-8")

    draft = f"""
## 第三章正文初稿

### 3 基于机器学习的目标频带条件预测模型

前两章建立了周期结构带隙分析的有限元计算基础，并明确了本文关注的目标频带优化问题。由于每一个候选结构均需要经过 COMSOL 频散计算才能获得可靠的带隙标签，若直接在大规模候选空间中反复调用有限元模型，将导致计算成本较高。为提高候选结构筛选效率，本章在 COMSOL 真实频散计算结果的基础上构建目标频带条件预测模型。需要强调的是，本章模型并不替代有限元分析，也不作为最终物理判据，而是用于在给定目标频带内对候选结构进行初步筛选和排序，为后续 COMSOL 复核及闭环遗传优化提供候选基础。

### 3.1 条件预测任务定义

本文将目标频带带隙预测写成条件预测问题。设结构参数为 x，结构族及形状描述为 s，目标频带为 B=[f_l, f_u]。模型输入由结构参数、形状统计特征和目标频带条件变量共同组成，输出包括目标频带内是否存在带隙重叠的概率 p_open，以及当带隙存在时的目标频带覆盖率预测值 c_hat。因此，本章采用的任务形式为：

    (x, s, B) -> (p_open, c_hat)

其中，p_open 对应分类标签 target_gap_is_open，c_hat 对应回归标签 target_gap_cover_ratio。数据集中同时保留 target_gap_overlap_Hz 字段，用于表示带隙与目标频带的真实重叠宽度。二者关系可理解为：target_gap_cover_ratio = target_gap_overlap_Hz / (target_band_high_Hz - target_band_low_Hz)。由于不同目标频带宽度可能不同，覆盖率能够更直接反映带隙对目标频带的相对覆盖程度，因此本文将 target_gap_cover_ratio 作为回归模型的主预测标签。

### 3.2 样本数据库构建与数据预处理

本章使用的样本数据库为 v12 版本数据集 windows_dense_v12_all_history_ga20_clean_v1。该数据集整合了历史目标频带数据、补充真值数据、主动学习数据以及 20 代 COMSOL 闭环遗传优化所得 active-band 真值。所有标签均来源于 COMSOL 频散计算或由其结果派生的目标频带重叠量，而不是由机器学习模型自行生成。

数据整理过程中，首先将不同阶段形成的历史数据集进行堆叠，并追加 20 代 GA 中通过 geometry_valid、contact_valid 和 solve_success 有效性筛选的 active-band 记录。清洗前共得到 {info['rows_stacked_before_cleaning']:,} 行记录，其中 20 代 GA 有效 COMSOL 源记录为 {info['rows_ga20_valid_source']:,} 条。随后，本文以 point_id、shape_id、结构参数以及目标频带上下限共同构造 physical_key，用于识别同一物理结构在不同数据版本中的重复记录。对于 physical_key 相同且标签一致的样本，仅保留一条代表记录；对于标签不一致的样本，优先保留优化来源频带与目标频带一致的 active-band 真值，并保留冲突审计记录。

经过物理键去重与冲突处理后，v12 数据集包含 {info['rows_clean_after_physical_key_dedup']:,} 条样本，覆盖 {info['unique_designs']:,} 个结构设计、{info['unique_shapes']:,} 个形状以及 {info['unique_families']:,} 个形状族。六个论文目标频带中，160-200 Hz 的正样本率和平均覆盖率相对较高，而 220-260 Hz 与 240-280 Hz 虽然存在较多正样本，但平均覆盖率仅约 0.020，说明高频段样本多为窄带重叠，不能仅凭是否打开判断其工程可用性。

### 3.3 条件分类模型与条件回归模型构建

本章采用两阶段预测结构。第一阶段为 HGB 分类器，用于判断目标频带内是否存在带隙重叠，输出 p_open；第二阶段为 HGB 回归器，仅在 target_gap_is_open=1 的正样本上训练，用于预测目标频带覆盖率 c_hat。模型输入包括结构几何参数、形状统计特征以及目标频带条件变量，其中目标频带条件变量包括 target_band_low_Hz、target_band_high_Hz、target_band_center_Hz 和 target_band_width_Hz。

采用两阶段模型的原因在于，目标频带预测同时包含“是否存在带隙”和“带隙覆盖程度”两个层次。若直接对所有样本回归覆盖率，大量零覆盖样本会弱化模型对正样本覆盖程度差异的学习；而先分类再回归，可以分别刻画带隙打开概率和覆盖率大小。最终用于候选排序时，可将 p_open 与 c_hat 组合为候选评分，使模型优先推荐既可能打开目标带隙、又具有较高覆盖率的结构。

### 3.4 模型评价指标

分类模型采用准确率、F1 值和平衡准确率作为评价指标。其中，F1 值综合考虑精确率和召回率，适用于正负样本不完全均衡的目标频带预测；平衡准确率进一步降低类别比例差异对评价结果的影响。回归模型采用 MAE、RMSE 和 R2 评价覆盖率预测误差。

为了检验模型泛化能力，本文采用两类交叉验证方式。第一类为按形状族分组的 Family-CV，用于评价模型面对未见结构族时的预测稳定性，是本章主要可信度依据。第二类为 leave-one-band 验证，即每次留出一个目标频带进行测试，用于检验模型对目标频带条件变化的外推能力。由于 leave-one-band 比常规分组验证更严格，其性能下降不表示模型失效，而说明本文预测模型应限定在预定义目标频带设计域内使用，不应表述为任意频带的通用外推器。

### 3.5 条件预测结果与候选筛选能力分析

在六个论文目标频带上，Family-CV 分类准确率为 {fmt(readiness['family_cv']['classifier']['accuracy'])}，F1 值为 {fmt(readiness['family_cv']['classifier']['f1'])}，平衡准确率为 {fmt(readiness['family_cv']['classifier']['balanced_accuracy'])}；覆盖率回归 MAE 为 {fmt(readiness['family_cv']['regressor_overall']['mae'], 4)}，R2 为 {fmt(readiness['family_cv']['regressor_overall']['r2'])}。该结果表明，在当前结构族和目标频带目录内，模型能够较稳定地学习结构参数、形状特征与目标频带带隙响应之间的统计关系。

在 leave-one-band 验证中，分类 F1 为 {fmt(readiness['leave_one_band']['classifier']['f1'])}，平衡准确率为 {fmt(readiness['leave_one_band']['classifier']['balanced_accuracy'])}，覆盖率回归 MAE 为 {fmt(readiness['leave_one_band']['regressor_overall']['mae'], 4)}，R2 为 {fmt(readiness['leave_one_band']['regressor_overall']['r2'])}。与 Family-CV 相比，leave-one-band 结果有所下降，说明目标频带变化会增加预测难度。其中，200-240 Hz 的留一频带分类 F1 较低，220-260 Hz 和 240-280 Hz 的平均覆盖率也较低，因此这些频带的结论应结合第四章和第五章的 COMSOL 真值进一步验证。

候选排序能力方面，本文将分类概率与覆盖率预测值组合为候选评分。在 Family-CV 中，Top-5 与 Top-10 候选的命中率均为 1.000，平均真实覆盖率分别为 0.731 和 0.732；在 leave-one-band 中，Top-5 与 Top-10 候选命中率也均为 1.000，平均真实覆盖率分别为 0.604 和 0.585。该结果说明，预测模型能够在候选集中将较高覆盖率样本前置，适合作为后续有限元复核和遗传算法搜索的初筛工具。但该结果不应解释为机器学习模型可以替代 COMSOL，最终结构性能仍需通过频散计算确认。

### 3.6 本章小结

本章基于 COMSOL 频散计算结果构建了目标频带条件预测模型，并形成 v12 版本训练数据集。该数据集整合历史目标频带数据、补充真值数据、主动学习数据和 20 代 COMSOL 闭环遗传优化 active-band 真值，通过 physical_key 完成重复样本识别和冲突处理。模型采用 HGB 分类器与 HGB 回归器的两阶段结构，分别预测目标频带带隙打开概率和覆盖率。

验证结果表明，在预定义目标频带目录和当前结构参数化空间内，模型具有一定的候选筛选和排序能力，可为后续优化提供初始候选和缩小搜索空间。然而，模型本质上仍是基于已有 COMSOL 标签的统计预测器，不能替代有限元物理计算。对于高频段和留一频带性能较弱的频带，后续章节需要进一步结合 COMSOL-in-loop GA 和代表性候选结构验证结果进行分析。
"""

    notes = """
## 第三章写作注意事项

### 可以作为第三章主结果

1. v12 数据集规模、数据来源整合、physical_key 去重和冲突处理结果。
2. HGB 分类器与 HGB 回归器的两阶段条件预测框架。
3. 六个论文目标频带上的 Family-CV 总体指标。
4. Top-k 候选排序能力，结论限定为“候选初筛和排序”。

### 只能作为补充说明

1. leave-one-band 结果：用于说明更严格外推检验，不宜作为模型强泛化主张。
2. 训练目录中的全 32 频带 metrics_summary：第三章主表应优先用 readiness 目录中过滤六个论文目标频带后的结果。
3. RF 900 棵树未完成全折训练的结果：只能说明曾尝试，不作为正式主结果。

### 需要避免的表述

1. 避免写“机器学习替代 COMSOL”。
2. 避免写“模型可任意预测连续频带”。
3. 避免只用 target_gap_is_open 宣称高频段优化成功。
4. 避免把 Top-k 命中率解释为最终结构真实性能。

### 需要第四章或第五章支撑的内容

1. 代表性结构的最终带隙覆盖范围和频散图。
2. 200-240 Hz、220-260 Hz、240-280 Hz 等困难频带的真实性能解释。
3. 预测器筛选候选与 COMSOL-in-loop GA 优化结果之间的对比。
4. 最终候选结构能否满足目标频带要求的物理验证。
"""

    formula_text = """
## 3.1 公式变量确认

根据真实训练标签，本章条件预测任务建议写为：

`(x, s, B) -> (p_open, c_hat)`

理由是正式回归器训练目标为 `target_gap_cover_ratio`，而不是 `target_overlap_Hz`。真实 overlap 字段名为 `target_gap_overlap_Hz`，数据集中未发现 `target_overlap_Hz`。二者关系为：

`target_gap_cover_ratio = target_gap_overlap_Hz / target_band_width_Hz`

其中 `target_band_width_Hz = target_band_high_Hz - target_band_low_Hz`。论文中可将 overlap 作为覆盖率的物理来源说明，但模型主回归输出建议记为 `c_hat`。
"""

    sections = [
        "# 第三章 v12 证据核对、图表路径与正文初稿",
        "## 1. v12 数据集文件核对",
        md_table(["文件路径", "是否存在", "行数或主要内容", "可用于论文哪一节", "备注"], file_inventory),
        "## 2. 字段定义核对",
        md_table(["字段", "是否存在", "含义", "证据位置"], field_rows),
        formula_text,
        "## 4. 模型训练、模型包与结果路径",
        md_table(["文件路径", "文件类型", "作用", "对应论文小节", "备注"], evidence_rows),
        "## 5. 第三章图表路径与图题建议",
        md_table(["PNG 路径", "SVG 路径", "论文图题建议"], figure_rows),
        "## 6. Word 可复制制表符表格",
        "\n\n".join(f"```text\n{table}\n```" for table in word_tables),
        draft,
        notes,
    ]
    report_path = OUT_DIR / "CH3_V12_EVIDENCE_TABLES_AND_DRAFT_CN.md"
    report_path.write_text("\n\n".join(sections), encoding="utf-8")
    print(report_path)
    print(OUT_DIR / "ch3_word_tables.tsv.txt")


if __name__ == "__main__":
    build_report()
