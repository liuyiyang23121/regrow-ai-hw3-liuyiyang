# backend/app/knowledge/store.py
# backend/app/knowledge/store.py
from typing import Dict, Any

class EnterpriseKnowledgeStore:
    """
    企业级数仓资产元数据字典与合规红线知识库 (2026 生产级)
    作用：防止数据智能体因幻觉写错物理字段，约束策略智能体避免公关合规风险。
    """
    
    # =====================================================================
    # 🌟 核心进化：多场景感知动态路由注入引擎
    # =====================================================================
    @staticmethod
    def get_context_by_scene(prompt: str) -> str:
        """
        根据前端下发的 prompt 指令，动态识别演练场景，注入最精准的元数据上下文。
        """
        prompt_lower = prompt.lower() if prompt else ""
        
        # 场景一：大促、连续购买、618
        if "连续" in prompt_lower or "618" in prompt_lower:
            return EnterpriseKnowledgeStore._get_scene_1_context()
            
        # 场景二：高危、全量重构、积分
        elif "积分" in prompt_lower or "registry" in prompt_lower:
            return EnterpriseKnowledgeStore._get_scene_2_context()
            
        # 场景三：半结构化、混乱日志
        elif "log" in prompt_lower and "json" in prompt_lower and "留学生" in prompt_lower:
            return EnterpriseKnowledgeStore._get_scene_3_context()
            
        # 🌟 新增场景四：流失预警高资产（绿色无阻通道）
        elif "churn_warning" in prompt_lower or "流失预警" in prompt_lower:
            return EnterpriseKnowledgeStore._get_scene_4_context()
            
        # 🌟 新增场景五：地理栅格灰度小流量
        elif "sh_011" in prompt_lower or "栅格" in prompt_lower or "limit" in prompt_lower:
            return EnterpriseKnowledgeStore._get_scene_5_context()
            
        # 🌟 新增场景六：跨境税收合规纠偏（文案红线）
        elif "代购" in prompt_lower or "免税" in prompt_lower or "关税" in prompt_lower:
            return EnterpriseKnowledgeStore._get_scene_6_context()
        # 场景七：人工双通道红线审核演练
        elif "审核" in prompt_lower or "hitl" in prompt_lower or "review" in prompt_lower:
            return EnterpriseKnowledgeStore._get_scene_7_context()            
        # 兜底
        return EnterpriseKnowledgeStore._get_default_context()

    # =====================================================================
    # 🔄 完美向下兼容：复活老代码硬编码所需的静态方法
    # =====================================================================
    @staticmethod
    def get_marketing_metadata_context() -> str:
        """向下兼容：提供基础数仓物理表拓扑结构"""
        return EnterpriseKnowledgeStore._get_default_context()

    @staticmethod
    def get_historical_best_practices() -> str:
        """向下兼容：提供历史红蓝对抗演化文案范式（解决 evo_agent.py 启动报错）"""
        return """
        [营销文案红线与金律知识库 - 默认兜底]
        - 黄金范式：采用【利益点前置】+【限时紧迫感催化】。
        - 驳回红线例证：禁止出现“大减价”、“100% 中奖”等引发合规投诉与公关危机的绝对化词汇。
        - 历史最佳案例：对 vip_level >= 5 的高价值流失预警客群，使用反思型文案比催促型文案点击率高 34%。
        """

    # =====================================================================
    # 📦 场景内部特化元数据数据集
    # =====================================================================
    @staticmethod
    def _get_scene_1_context() -> str:
        """【场景一】大促高价值客群连续购买拓扑"""
        return """
        [元数据对齐 - 场景一：大促连续购买域]
        1. 物理表名: `user_order_df` (全量电商交易流水表)
           - 字段: `user_id` (varchar, 用户加密混淆 ID)
           - 字段: `order_id` (varchar, 订单唯一序列号)
           - 字段: `payment_amount` (decimal(10,2), 实付金额，筛选客单价需 > 500)
           - 字段: `pay_time` (timestamp, 支付时间戳，格式 'YYYY-MM-DD HH:MM:SS')
           - 💡【大厂指引】：计算“连续 3 天购买”必须使用窗口函数 LEAD/LAG 或 DENSE_RANK() 进行时间截断差值计算。

        2. 历史文案金律 (红蓝对抗最佳范式):
           - 核心结论：针对大促高价值活跃客群，禁止轰炸式营销。
           - 黄金模板：【尊崇身份认同】+【专享通道】（例如：“尊敬的 V5 会员，您的 618 极速发货通道已就绪...”）。反思型触达点击率比常规大流催单高 34%。
        """

    @staticmethod
    def _get_scene_2_context() -> str:
        """【场景二】生产环境高危等级与积分基础表（带有明显的 HITL 触发钩子）"""
        return """
        [元数据对齐 - 场景二：核心资产高危变更域]
        1. 物理表名: `user_points_registry` (全量会员积分资产底表 - 极度高危)
           - 字段: `user_id` (varchar, 唯一标识)
           - 字段: `vip_level` (int, 尊享等级，范围 1-7)
           - 字段: `current_points` (bigint, 账户当前可用积分，不可轻易归零)
           - 字段: `last_update_operator` (string, 变更操作人 ERP 账号)
           - 🚨【安全围栏红线】：任何对该表不带 WHERE 条件的 UPDATE、或者涉及全表行数超过 10,000 行的 DELETE 操作，数据安全智能体（Brake Agent）必须启动异步熔断，输出 'hitl_brake' 信号拦截下发！
        """

    @staticmethod
    def _get_scene_3_context() -> str:
        """【场景三】非结构化 ODS 层脏日志 JSON 字段表"""
        return """
        [元数据对齐 - 场景三：非结构化混乱日志域]
        1. 物理表名: `user_behavior_log` (埋点多维半结构化日志表)
           - 字段: `log_id` (bigint, 自增流水)
           - 字段: `event_name` (string, 事件名，如 'page_view', 'click_banner')
           - 字段: `context` (string/json, 核心脏数据字段，格式为字符串嵌套 JSON)
             - JSON 内部键路径解析: 
               * 提取城市/大区: `$.device_info.location.region` (可能返回 '华东', '海外' 等不规范文本)
               * 提取留学生标签: `$.user_profile.tags.education_status` (值可能为 'overseas_student')
           - 💡【大厂指引】：Hive/Presto 环境下必须使用 get_json_object(context, '$.path') 或 json_extract_scalar 函数进行安全解析，注意做乱码 NULL 值过滤。
           
        2. 跨境电商跨境文案合规红线:
           - 🚨【合规红线】：涉及海外留学生和跨境优惠券，文案绝对不可提及“偷税”、“免税代购”等敏感字眼，必须符合国家海关总署最新跨境电商税收合规标准。
        """

    # =====================================================================
    # 📦 新增场景的元数据特化数据集
    # =====================================================================
    @staticmethod
    def _get_scene_4_context() -> str:
        """【场景四特化】绿色低风险通道上下文"""
        return """
        [元数据对齐 - 场景四：高预警低风险查询]
        1. 适用准则：只读基础视图，预计影响行数 < 500 行，属于完全安全的业务策略圈选。
        2. 物理拓扑: 基于标准基础表 `user_base_df`。
           - 筛选条件：`lifecycle_status = 'churn_warning' AND vip_level >= 5`
        3. 安全围栏批注：无任何 DML 写操作风险。安全智能体（Brake Agent）应当一路无阻放行，100% 直达下游。
        """

    @staticmethod
    def _get_scene_5_context() -> str:
        """【场景五特化】小流量灰度网格上下文"""
        return """
        [元数据对齐 - 场景五：小流量地域灰度]
        1. 适用准则：包含了 LIMIT 限制子句的探索性 SQL，单次计算开销极低。
        2. 核心语法提示：在关联 `user_base_df` 和 `marketing_campaign_logs` 时，必须确保有 `LIMIT 1000` 限制。
        3. 安全围栏批注：尽管涉及沉睡 VIP 关联，但带有明确的小流量锁（Limit），安全智能体识别后应直接给予绿色豁免权，顺畅吐出资产。
        """

    @staticmethod
    def _get_scene_6_context() -> str:
        """【场景六特化】跨境文案合规合规审查上下文"""
        return """
        [元数据对齐 - 场景六：海关合规公关防御域]
        1. 业务红线：严禁在策略文案中出现“代购”、“免税”、“偷税规避”等容易被监管处罚的灰色词汇。
        2. 安全围栏熔断策略：数据智能体生成的 SQL 虽然合法，但一旦后半程策略智能体生成包含上述违规词的文案时，安全防护智能体（Brake Agent）必须**在文案审查节点启动熔断**，并向前端发送拦截信号，向用户展示人工修正弹窗！
        """

    @staticmethod
    def _get_scene_7_context() -> str:
        """【场景七】人工双通道红线审核与差异化对比演练"""
        return """
        [元数据对齐 - 场景七：人工智能与人工干预（HITL）对抗域]
        1. 核心变更风险：该场景属于高敏感营销文案触达或核心资产批量修改。
        2. 安全熔断规则：
           - 数据/策略智能体生成的方案必须强制进入 `PENDING_REVIEW`（待审核）状态。
           - 拦截钩子信号：`trigger_hitl_brake`
        3. 演练对照组：
           - 【若人工审核通过】：允许方案下发生产环境，执行数据回溯与灰度触达。
           - 【若人工审核不通过】：彻底熔断当前工作流，触发智能体自我迭代或人工修正弹窗。
        """
    
    @staticmethod
    def _get_default_context() -> str:
        """默认常规元数据"""
        return """
        [企业级数仓营销域字典架构声明 - 基础通用版]
        1. 物理表名: `user_base_df` (高价值核心客群流失预警表)
           - 字段: `user_id` (varchar, 用户唯一加密混淆 ID)
           - 字段: `last_active_date` (date, 最后一次活跃日期，格式 'YYYY-MM-DD')
           - 字段: `lifecycle_status` (string, 枚举值: 'active'活跃, 'churn_warning'流失预警, 'lost'已流失)
           - 字段: `vip_level` (int, 尊享等级，范围 1-7)
           - 字段: `geo_city` (string, 注册常驻城市编码)
        """