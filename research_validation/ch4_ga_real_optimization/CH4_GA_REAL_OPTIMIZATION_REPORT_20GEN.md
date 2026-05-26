# 绗?绔?鍩轰簬鐪熷疄棰戞暎璁＄畻鐨勭洰鏍囬甯﹂仐浼犱紭鍖栨柟娉曪紙20浠ｇ粨鏋滐級

鏈姤鍛婃暣鐞嗙4绔犳墍闇€鐨勭湡瀹?COMSOL 棰戞暎璁＄畻椹卞姩閬椾紶绠楁硶鏉愭枡銆傜4绔犲彧璁ㄨ鈥滃熀浜?COMSOL 鐪熷疄棰戞暎璁＄畻鐨勯棴鐜仐浼犱紭鍖栤€濓紝閫傚簲搴﹀嚱鏁颁笉浣跨敤鏈哄櫒瀛︿範棰勬祴鍊笺€傛満鍣ㄥ涔犵瓫閫夈€侀殢鏈哄€欓€変笌鐪熷疄 GA 鐨勫姣斿簲鏀惧叆绗?绔犮€?

## 4.1 鐩爣棰戝甫缁撴瀯浼樺寲闂鍒楀紡

璁惧崟鑳炵粨鏋勮璁″彉閲忎负 $\mathbf x$锛岀洰鏍囬甯︿负 $B_t=[f_l,f_u]$銆傚姣忎釜鍊欓€夌粨鏋勶紝閫氳繃 COMSOL 璁＄畻棰戞暎鍏崇郴骞舵彁鍙栫3-4闃朵箣闂寸殑甯﹂殭杈圭晫 $[g_l(\mathbf x),g_u(\mathbf x)]$銆傜洰鏍囬甯﹂噸鍙犲搴﹀畾涔変负锛?

$$
J(\mathbf x)=\max\left(0,\min(g_u(\mathbf x), f_u)-\max(g_l(\mathbf x), f_l)\right)
$$

鐩爣棰戝甫瑕嗙洊鐜囧畾涔変负锛?

$$
C(\mathbf x)=\frac{J(\mathbf x)}{f_u-f_l}
$$

鏈珷浼樺寲鐩爣涓烘渶澶у寲鐪熷疄棰戞暎璁＄畻寰楀埌鐨勭洰鏍囬甯﹂噸鍙犲搴︼細

$$
\mathbf x^*=\arg\max_{\mathbf x\in\Omega} J(\mathbf x)
$$

鍏朵腑 $\Omega$ 涓烘弧瓒冲弬鏁拌寖鍥淬€佸嚑浣曟湁鏁堟€с€佹帴瑙︽湁鏁堟€т笌鎴愬姛姹傝В瑕佹眰鐨勮璁＄┖闂淬€?

## 4.2 璁捐鍙橀噺銆佺害鏉熸潯浠朵笌閫傚簲搴﹀嚱鏁?

璁捐鍙橀噺鍖呮嫭绂绘暎褰㈢姸鍩哄洜 `shape_id` 涓庤繛缁舰鐘跺弬鏁?`a1, a2, b1, b2, a3, b3, a4, b4, a5, b5, r0`銆傚彉閲忚寖鍥磋 `ch4_design_variables.csv`锛岀害鏉熸潯浠惰 `ch4_constraints.csv`銆?

| variable_name | physical_meaning | variable_type | lower_bound | upper_bound | used_in_ga | note |
| --- | --- | --- | --- | --- | --- | --- |
| shape_id | 鍗曡優澶规潅杞粨/缁撴瀯鏃忕鏁ｅ熀鍥?| categorical | shape_pool鍊欓€夐泦鍚?| 54涓€欓€夎疆寤?| True | 褰㈢姸鍩哄洜鏉ヨ嚜棰勭瓫閫夎疆寤撳簱锛岄潪杩炵画鍙傛暟 |
| a1 | 涓€闃朵綑寮﹀舰鐘跺弬鏁?| continuous | 0.4600 | 0.5400 | True | clip_to_bounds绾︽潫鍦ㄥ叏灞€涓婁笅闄愬唴 |
| a2 | 浜岄樁浣欏鸡褰㈢姸鍙傛暟 | continuous | -0.1800 | -0.0600 | True | clip_to_bounds绾︽潫鍦ㄥ叏灞€涓婁笅闄愬唴 |
| b1 | 涓€闃舵寮﹀舰鐘跺弬鏁?| continuous | -0.0500 | 0.0500 | True | clip_to_bounds绾︽潫鍦ㄥ叏灞€涓婁笅闄愬唴 |
| b2 | 浜岄樁姝ｅ鸡褰㈢姸鍙傛暟 | continuous | 0 | 0.0800 | True | clip_to_bounds绾︽潫鍦ㄥ叏灞€涓婁笅闄愬唴 |
| a3 | 涓夐樁浣欏鸡褰㈢姸鍙傛暟 | continuous | -0.0400 | 0.0400 | True | clip_to_bounds绾︽潫鍦ㄥ叏灞€涓婁笅闄愬唴 |
| b3 | 涓夐樁姝ｅ鸡褰㈢姸鍙傛暟 | continuous | -0.0400 | 0.0400 | True | clip_to_bounds绾︽潫鍦ㄥ叏灞€涓婁笅闄愬唴 |
| a4 | 鍥涢樁浣欏鸡褰㈢姸鍙傛暟 | continuous | -0.0300 | 0.0300 | True | clip_to_bounds绾︽潫鍦ㄥ叏灞€涓婁笅闄愬唴 |
| b4 | 鍥涢樁姝ｅ鸡褰㈢姸鍙傛暟 | continuous | -0.0300 | 0.0300 | True | clip_to_bounds绾︽潫鍦ㄥ叏灞€涓婁笅闄愬唴 |
| a5 | 浜旈樁浣欏鸡褰㈢姸鍙傛暟 | continuous | -0.0200 | 0.0200 | True | clip_to_bounds绾︽潫鍦ㄥ叏灞€涓婁笅闄愬唴 |
| b5 | 浜旈樁姝ｅ鸡褰㈢姸鍙傛暟 | continuous | -0.0200 | 0.0200 | True | clip_to_bounds绾︽潫鍦ㄥ叏灞€涓婁笅闄愬唴 |
| r0 | 鍩哄噯鍗婂緞/灏哄害鍙傛暟 | continuous | 0.0100 | 0.0140 | True | clip_to_bounds绾︽潫鍦ㄥ叏灞€涓婁笅闄愬唴 |

绾︽潫鏉′欢濡備笅锛?

| constraint_name | mathematical_form | implementation | role_in_ga |
| --- | --- | --- | --- |
| parameter_range_constraint | x_j in [lower_j, upper_j] | 杩炵画鍙橀噺浜ゅ弶鍜屽彉寮傚悗閫氳繃 clip_to_bounds 鎴柇鍒?globalBounds | 闄愬畾璁捐鍙橀噺鍙鍩?|
| geometry_valid constraint | geometry_valid = 1 | 鍑犱綍鏃犳晥鏃?fitness = failurePenaltyGeometry | 鎺掗櫎涓嶅彲寤烘ā鍑犱綍 |
| contact_valid constraint | contact_valid = 1 | 鎺ヨЕ鏃犳晥鏃?fitness = failurePenaltyContact | 淇濊瘉澶规潅/鍩轰綋鎺ヨЕ鍏崇郴婊¤冻璁＄畻瑕佹眰 |
| solve_success constraint | solve_success = 1 | COMSOL 姹傝В澶辫触鏃?fitness = failurePenaltySolve | 淇濊瘉棰戞暎缁撴灉鍙敤浜庨€傚簲搴﹁瘎浠?|
| target_overlap_Hz > 0 active constraint | target_overlap_Hz > 0 | 缁熻鏈夋晥鍊欓€夋椂浣跨敤锛屼笉浣滀负纭害鏉燂紱閫傚簲搴︾洿鎺ユ渶澶у寲 target_overlap_Hz | 瀹氫箟鏈夋晥鍊欓€夊苟琛￠噺鐩爣棰戝甫鍛戒腑鎯呭喌 |

閫傚簲搴﹀嚱鏁板悕绉颁负 `target_overlap_Hz`锛屾鏂囪В閲婁负鈥滅洰鏍囬甯﹂噸鍙犲搴︹€濄€傝嫢鍑犱綍銆佹帴瑙︽垨姹傝В澶辫触锛屽垯閫氳繃鎯╃綒閫傚簲搴﹀鐞嗭紱鎴愬姛姹傝В鐨勫€欓€夋寜鐪熷疄鐩爣棰戝甫閲嶅彔瀹藉害鎺掑簭銆?

## 4.3 COMSOL 棰戞暎璁＄畻涓庣洰鏍囬甯﹂噸鍙犲搴︽彁鍙?

姣忎釜 GA 涓綋棣栧厛鐢卞舰鐘跺熀鍥犲拰杩炵画鍙傛暟鐢熸垚鍗曡優缁撴瀯锛岀劧鍚庤皟鐢?COMSOL 棰戞暎璁＄畻銆傝绠楀畬鎴愬悗锛屼粠棰戞暎鏇茬嚎涓彁鍙栧甫闅欎笂涓嬭竟鐣岋紝骞朵笌鐩爣棰戝甫姹備氦锛屽緱鍒?`target_overlap_Hz` 涓?`cover_ratio`銆傚浘4-2缁欏嚭浜嗗崟涓釜浣撶殑鐪熷疄璇勪环娴佺▼銆?

鍙敤鍥句欢锛?

- 鍥?-1锛歚figures/ch4_fig4_1_real_ga_flowchart.png`
- 鍥?-2锛歚figures/ch4_fig4_2_comsol_evaluation_flowchart.png`

## 4.4 閬椾紶绠楁硶鎼滅储娴佺▼

鏈珷閲囩敤鍏釜鐙珛鐩爣棰戝甫鐨勭湡瀹為棴鐜仐浼犱紭鍖栫粨鏋滐紝姣忎釜鐩爣棰戝甫鍧囬噰鐢ㄦ渶鏂?0浠ｇ粨鏋溿€傜缇よ妯′负6锛屽疄闄呮瘡涓畬鏁撮甯﹁瘎浠?20娆°€備唬鏁扮紪鍙蜂负1-20锛屼笉瀛樺湪0-19缂栧彿璇垽銆?

閬椾紶鎿嶄綔鍖呮嫭锛?

- 鍒濆鍖栵細浠庨绛涢€夊舰鐘跺簱鍜屽弬鏁拌寖鍥寸敓鎴愬垵濮嬬缇わ紱
- 閫夋嫨锛氶敠鏍囪禌閫夋嫨锛岄敠鏍囪禌瑙勬ā涓?min(3, 褰撳墠绉嶇兢鏁?锛?
- 浜ゅ弶锛氳繛缁彉閲忛噰鐢ㄥ弻浜茬嚎鎬х粍鍚堬紝褰㈢姸鍩哄洜浠庡弻浜蹭腑浜岄€変竴锛?
- 鍙樺紓锛氬舰鐘跺熀鍥犳寜 `shapeMutationRate` 闅忔満鏇挎崲锛岃繛缁彉閲忔寜 `continuousMutationRate` 鍔犻珮鏂壈鍔ㄥ苟鎴柇鍒板弬鏁拌寖鍥达紱
- 绮捐嫳淇濈暀锛氭瘡浠ｄ繚鐣欓€傚簲搴︽渶楂樼殑 `eliteCount=2` 涓釜浣擄紱
- 缁堟鏉′欢锛氳揪鍒?`maxGenerations=20`锛屾湰鎵圭粨鏋滃潎鏈惎鐢ㄦ棭鍋溿€?

閬椾紶绠楁硶鍙傛暟琛細

| target_band | target_band_tag | population_size | n_generations_actual | generation_min | generation_max | unique_generation_count | max_generations_config | n_evaluations_actual | expected_evaluations | selection_method | crossover_probability | mutation_probability | elite_count_or_ratio | random_seed | termination_condition | fitness_function_name | continuous_mutation_scale | shape_pool_mode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 140-180 Hz | band140_180 | 6 | 20 | 1 | 20 | 20 | 20 | 120 | 120 | 閿︽爣璧涢€夋嫨锛岄敠鏍囪禌瑙勬ā=min(3, 褰撳墠绉嶇兢鏁? | 杩炵画鍙橀噺闈炵簿鑻变釜浣撴瘡娆″潎鍋氬弻浜茬嚎鎬х粍鍚堬紱褰㈢姸鍩哄洜浠庡弻浜蹭簩閫変竴 | 褰㈢姸鍩哄洜 0.2; 杩炵画鍙橀噺 0.25 | 2 | 20260404.0000 | 杈惧埌 maxGenerations=20; enableEarlyStop=False | target_overlap_Hz / 鐩爣棰戝甫閲嶅彔瀹藉害 | 0.1000 | stage1_screened |
| 160-200 Hz | band160_200 | 6 | 20 | 1 | 20 | 20 | 20 | 120 | 120 | 閿︽爣璧涢€夋嫨锛岄敠鏍囪禌瑙勬ā=min(3, 褰撳墠绉嶇兢鏁? | 杩炵画鍙橀噺闈炵簿鑻变釜浣撴瘡娆″潎鍋氬弻浜茬嚎鎬х粍鍚堬紱褰㈢姸鍩哄洜浠庡弻浜蹭簩閫変竴 | 褰㈢姸鍩哄洜 0.2; 杩炵画鍙橀噺 0.25 | 2 | 20260404.0000 | 杈惧埌 maxGenerations=20; enableEarlyStop=False | target_overlap_Hz / 鐩爣棰戝甫閲嶅彔瀹藉害 | 0.1000 | stage1_screened |
| 180-220 Hz | band180_220 | 6 | 20 | 1 | 20 | 20 | 20 | 120 | 120 | 閿︽爣璧涢€夋嫨锛岄敠鏍囪禌瑙勬ā=min(3, 褰撳墠绉嶇兢鏁? | 杩炵画鍙橀噺闈炵簿鑻变釜浣撴瘡娆″潎鍋氬弻浜茬嚎鎬х粍鍚堬紱褰㈢姸鍩哄洜浠庡弻浜蹭簩閫変竴 | 褰㈢姸鍩哄洜 0.2; 杩炵画鍙橀噺 0.25 | 2 | 20260404.0000 | 杈惧埌 maxGenerations=20; enableEarlyStop=False | target_overlap_Hz / 鐩爣棰戝甫閲嶅彔瀹藉害 | 0.1000 | stage1_screened |
| 200-240 Hz | band200_240 | 6 | 20 | 1 | 20 | 20 | 20 | 120 | 120 | 閿︽爣璧涢€夋嫨锛岄敠鏍囪禌瑙勬ā=min(3, 褰撳墠绉嶇兢鏁? | 杩炵画鍙橀噺闈炵簿鑻变釜浣撴瘡娆″潎鍋氬弻浜茬嚎鎬х粍鍚堬紱褰㈢姸鍩哄洜浠庡弻浜蹭簩閫変竴 | 褰㈢姸鍩哄洜 0.2; 杩炵画鍙橀噺 0.25 | 2 | 20260404.0000 | 杈惧埌 maxGenerations=20; enableEarlyStop=False | target_overlap_Hz / 鐩爣棰戝甫閲嶅彔瀹藉害 | 0.1000 | stage1_screened |
| 220-260 Hz | band220_260 | 6 | 20 | 1 | 20 | 20 | 20 | 120 | 120 | 閿︽爣璧涢€夋嫨锛岄敠鏍囪禌瑙勬ā=min(3, 褰撳墠绉嶇兢鏁? | 杩炵画鍙橀噺闈炵簿鑻变釜浣撴瘡娆″潎鍋氬弻浜茬嚎鎬х粍鍚堬紱褰㈢姸鍩哄洜浠庡弻浜蹭簩閫変竴 | 褰㈢姸鍩哄洜 0.2; 杩炵画鍙橀噺 0.25 | 2 | 20260404.0000 | 杈惧埌 maxGenerations=20; enableEarlyStop=False | target_overlap_Hz / 鐩爣棰戝甫閲嶅彔瀹藉害 | 0.1000 | stage1_screened |
| 240-280 Hz | band240_280 | 6 | 20 | 1 | 20 | 20 | 20 | 120 | 120 | 閿︽爣璧涢€夋嫨锛岄敠鏍囪禌瑙勬ā=min(3, 褰撳墠绉嶇兢鏁? | 杩炵画鍙橀噺闈炵簿鑻变釜浣撴瘡娆″潎鍋氬弻浜茬嚎鎬х粍鍚堬紱褰㈢姸鍩哄洜浠庡弻浜蹭簩閫変竴 | 褰㈢姸鍩哄洜 0.2; 杩炵画鍙橀噺 0.25 | 2 | 20260404.0000 | 杈惧埌 maxGenerations=20; enableEarlyStop=False | target_overlap_Hz / 鐩爣棰戝甫閲嶅彔瀹藉害 | 0.1000 | stage1_screened |

## 4.5 涓嶅悓鐩爣棰戝甫涓嬬殑鐪熷疄浼樺寲缁撴灉

鍏釜鐩爣棰戝甫鏈€缁堝潎閲囩敤20浠ｇ湡瀹?GA 杈撳嚭鐩綍锛屾眹鎬荤粨鏋滃涓嬶細

| target_band | n_generations_actual | n_evaluations_actual | n_solve_success | solve_success_rate | n_active_overlap | active_rate | best_target_overlap_Hz | best_cover_ratio | best_gap_lower_Hz | best_gap_upper_Hz | best_generation | is_20gen_complete |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 140-180 Hz | 20 | 120 | 108 | 0.9000 | 105 | 0.9722 | 22.2665 | 0.5567 | 157.7335 | 180.0073 | 19 | True |
| 160-200 Hz | 20 | 120 | 112 | 0.9333 | 112 | 1.0000 | 32.4455 | 0.8111 | 167.5545 | 200.0512 | 20 | True |
| 180-220 Hz | 20 | 120 | 111 | 0.9250 | 107 | 0.9640 | 40.0000 | 1.0000 | 178.8248 | 220.6533 | 18 | True |
| 200-240 Hz | 20 | 120 | 109 | 0.9083 | 98 | 0.8991 | 35.2829 | 0.8821 | 188.6648 | 235.2829 | 19 | True |
| 220-260 Hz | 20 | 120 | 106 | 0.8833 | 102 | 0.9623 | 4.0976 | 0.1024 | 244.3921 | 248.4897 | 20 | True |
| 240-280 Hz | 20 | 120 | 105 | 0.8750 | 105 | 1.0000 | 3.9345 | 0.0984 | 245.0751 | 249.0096 | 20 | True |

鍙敤鍥句欢锛?

- 鍥?-3锛歚figures/ch4_fig4_3_ga_convergence_20gen.png`
- 鍥?-4锛歚figures/ch4_fig4_4_best_overlap_bar_20gen.png`
- 鍥?-5锛歚figures/ch4_fig4_5_success_active_rates_20gen.png`
- 鍥?-6锛歚figures/ch4_fig4_6_best_unit_cells_6bands.png`
- 鍥?-7锛歚figures/ch4_fig4_7_representative_dispersion_3bands.png`

鍏稿瀷妗堜緥瑙?`ch4_typical_cases_20gen.md`銆傚叾涓?180-220 Hz 涓轰腑棰戞垚鍔熸渚嬶紝200-240 Hz 涓轰腑楂橀妗堜緥锛?40-280 Hz 涓洪珮棰戝洶闅炬渚嬨€?

### 12浠ｅ埌20浠ｆ敼杩?

| target_band | target_band_tag | generation_numbering | best_overlap_at_gen12 | best_overlap_at_gen20 | improvement_Hz | improvement_ratio | best_generation_12_or_before | best_generation_20 | new_best_in_gen13_to20 | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 140-180 Hz | band140_180 | 1-20 | 20.7394 | 22.2665 | 1.5271 | 0.0736 | 12 | 19 | True | 浠庢墍閲囩敤20浠ｇ洰褰曠殑history鎭㈠锛沢eneration缂栧彿涓?-20 |
| 160-200 Hz | band160_200 | 1-20 | 30.0720 | 32.4455 | 2.3736 | 0.0789 | 12 | 20 | True | 浠庢墍閲囩敤20浠ｇ洰褰曠殑history鎭㈠锛沢eneration缂栧彿涓?-20 |
| 180-220 Hz | band180_220 | 1-20 | 36.9014 | 40.0000 | 3.0986 | 0.0840 | 12 | 18 | True | 浠庢墍閲囩敤20浠ｇ洰褰曠殑history鎭㈠锛沢eneration缂栧彿涓?-20 |
| 200-240 Hz | band200_240 | 1-20 | 31.3800 | 35.2829 | 3.9030 | 0.1244 | 12 | 19 | True | 浠庢墍閲囩敤20浠ｇ洰褰曠殑history鎭㈠锛沢eneration缂栧彿涓?-20 |
| 220-260 Hz | band220_260 | 1-20 | 2.8682 | 4.0976 | 1.2294 | 0.4286 | 12 | 20 | True | 浠庢墍閲囩敤20浠ｇ洰褰曠殑history鎭㈠锛沢eneration缂栧彿涓?-20 |
| 240-280 Hz | band240_280 | 1-20 | 3.0016 | 3.9345 | 0.9328 | 0.3108 | 12 | 20 | True | 浠庢墍閲囩敤20浠ｇ洰褰曠殑history鎭㈠锛沢eneration缂栧彿涓?-20 |

鍥句欢锛歚figures/ch4_ga_12gen_vs_20gen_overlap.png`銆?

## 4.6 鏈珷灏忕粨

1. 鍏釜鐩爣棰戝甫鍧囧凡鏁寸悊涓?0浠ｇ湡瀹?GA 缁撴灉锛屾瘡涓畬鏁撮甯﹀疄闄呰瘎浠锋鏁颁负120娆°€?
2. 180-220 Hz 鐩爣棰戝甫鍦?0浠ｅ唴杈惧埌40 Hz閲嶅彔瀹藉害锛岀洰鏍囬甯﹁鐩栫巼涓?.0锛屾槸鏈€娓呮櫚鐨勪腑棰戞垚鍔熸渚嬨€?
3. 160-200 Hz 涓?00-240 Hz 涔熻幏寰楄緝楂樿鐩栫巼锛岃鏄庣湡瀹為鏁ｈ绠楅┍鍔ㄧ殑 GA 鑳藉鍦ㄤ腑棰戝拰涓珮棰戝尯鍩熸寔缁敼杩涚粨鏋勩€?
4. 220-260 Hz 涓?40-280 Hz 鐨勬渶缁堥噸鍙犲搴︿粛杈冨皬锛岃鏄庨珮棰戠洰鏍囨洿鍙楃粨鏋勬棌涓庡弬鏁板寲琛ㄨ揪闄愬埗锛涚户缁鍔犱唬鏁板彲鑳藉甫鏉ュ眬閮ㄦ敼鍠勶紝浣嗘洿鍙兘闇€瑕佹墿灞曞舰鐘舵満鍒舵垨鍊欓€夌粨鏋勬棌銆?
5. 鏈珷缁撴灉鍙瘉鏄庣湡瀹?COMSOL 棰戞暎璁＄畻椹卞姩鐨勯仐浼犱紭鍖栬繃绋嬩笌鏁堟灉锛屼笉娣峰叆鏈哄櫒瀛︿範棰勬祴閫傚簲搴︼紱鏈哄櫒瀛︿範鍊欓€夌瓫閫夊姣斿簲鍦ㄧ5绔犲崟鐙睍寮€銆?
