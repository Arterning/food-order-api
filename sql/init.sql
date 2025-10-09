-- Initial admin user (password: goodlife123)
INSERT INTO "user" (id, username, password_hash) VALUES (1, 'admin', 'scrypt:32768:8:1$Hdo9fJPIyJFSLDJN$ec5b3984b0083bbc475f47f7864fa17f7d11d9a8e1ae32c53d1a5093668dc9086e1cd048591981b83869f66b0aedb11626865de4ee8f0f2e3c0ac263f098712c');

-- Initial recipe data
INSERT INTO recipe (id, name, category, image, ingredients) VALUES
(1, '红烧肉', 'dish', 'https://picsum.photos/seed/hongshaorou/300/200', '五花肉、酱油、冰糖'),
(2, '宫保鸡丁', 'dish', 'https://picsum.photos/seed/gongbaojiding/300/200', '鸡肉、花生米、干辣椒'),
(3, '清蒸鱼', 'dish', 'https://picsum.photos/seed/qingzhengyu/300/200', '鱼、姜片、葱段'),
(4, '番茄炒蛋', 'dish', 'https://picsum.photos/seed/fanqiechaodan/300/200', '番茄、鸡蛋、葱花'),
(5, '麻婆豆腐', 'dish', 'https://picsum.photos/seed/mapotofu/300/200', '豆腐、肉末、豆瓣酱'),
(6, '白米饭', 'main', 'https://picsum.photos/seed/mifan/300/200', '大米'),
(7, '馒头', 'main', 'https://picsum.photos/seed/mantou/300/200', '面粉、酵母'),
(8, '西红柿鸡蛋汤', 'soup', 'https://picsum.photos/seed/xihongshitang/300/200', '番茄、鸡蛋、葱花'),
(9, '西瓜', 'dessert', 'https://picsum.photos/seed/xigua/300/200', '西瓜'),
(10, '可乐', 'drink', 'https://picsum.photos/seed/kele/300/200', '可乐');