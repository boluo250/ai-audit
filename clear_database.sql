-- 清空project_task表数据
DELETE FROM "public"."project_task";

-- 重置序列
ALTER SEQUENCE project_task_id_seq RESTART WITH 1;

-- 显示清空结果
SELECT 'Database cleared successfully' AS status;
