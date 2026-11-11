export const roleLabels:Record<string,string>={admin:'决策复核人',analyst:'空间分析员',viewer:'巡护观察员'};
export const statusLabels:Record<string,string>={queued:'排队中',running:'推演中',completed:'已完成',failed:'失败',pending:'待复核',approved:'已批准',rejected:'已退回',applied:'已生效',quarantined:'含隔离行'};
export const quarantineReasonLabels:Record<string,string>={missing_columns:'缺少必需列',invalid_coordinate:'坐标无效或越界',invalid_weight:'权重无效或为负',invalid_surveyed_at:'采测时间无法解析',empty_site_id:'样点编号为空',empty_label:'样点名称为空',duplicate_in_batch:'同批编号重复',dataset_capacity_exceeded:'超出5000点上限',surveyed_at_not_newer:'采测时间不晚于现行记录，已忽略'};
export const earthRadiusKm=6371.0088;
