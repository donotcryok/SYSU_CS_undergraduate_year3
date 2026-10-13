function bit_plane_analysis()
% 主函数：执行位平面分析和图像隐写实验的完整流程

    % 创建结果目录
    if ~exist('result', 'dir')
        mkdir('result');
    end

    % 尝试多个可能的图像路径
    possible_paths = {
        '../img/c.jpg', 
        'img/c.jpg', 
        '../c.jpg', 
        'c.jpg'
    };
    
    original_image = [];
    used_path = '';
    
    fprintf('正在尝试读取图像...\n');
    for i = 1:length(possible_paths)
        path = possible_paths{i};
        fprintf('尝试路径: %s\n', path);
        if exist(path, 'file')
            original_image = imread(path);
            if ~isempty(original_image)
                % 如果是彩色图像，转换为灰度
                if size(original_image, 3) == 3
                    original_image = rgb2gray(original_image);
                end
                used_path = path;
                fprintf('成功从路径读取图像: %s\n', path);
                break;
            else
                fprintf('文件存在但无法读取: %s\n', path);
            end
        else
            fprintf('文件不存在: %s\n', path);
        end
    end
    
    % 错误处理：无法读取图像
    if isempty(original_image)
        fprintf('\n=== 错误：无法读取图像 ===\n');
        fprintf('请检查以下事项：\n');
        fprintf('1. 确保图像文件 ''c.jpg'' 存在\n');
        fprintf('2. 将图像文件放在以下任一位置：\n');
        for i = 1:length(possible_paths)
            abs_path = fullfile(pwd, possible_paths{i});
            fprintf('   - %s\n', abs_path);
        end
        fprintf('3. 确保图像文件格式正确且未损坏\n');
        fprintf('\n当前工作目录: %s\n', pwd);
        return;
    end
    
    fprintf('成功读取图像，尺寸: %s\n', mat2str(size(original_image)));
    fprintf('使用的路径: %s\n', used_path);
    
    % 步骤1: 提取8个位平面
    fprintf('\n正在提取位平面...\n');
    bit_planes = extract_bit_planes(original_image);
    
    % 单独显示每个位平面
    fprintf('单独显示各位平面...\n');
    show_bit_planes_individually(bit_planes);
    
    % 显示所有位平面的综合图
    plot_all_bit_planes(original_image, bit_planes, 'result/bit_planes_all.png');
    
    % 步骤2: 图像隐写实验 - 修改最低位平面
    fprintf('\n进行图像隐写实验...\n');
    
    % 测试4种不同的修改模式
    modification_patterns = {'random', 'checkerboard', 'zeros', 'ones'};
    
    for i = 1:length(modification_patterns)
        pattern = modification_patterns{i};
        fprintf('\n--- 修改模式: %s ---\n', pattern);
        
        % 修改最低位平面
        modified_image = modify_lsb_plane(original_image, pattern);
        
        % 计算修改前后的差异
        [diff_img, mse, max_diff] = calculate_difference(original_image, modified_image);
        
        % 显示对比结果
        plot_steganography_comparison(original_image, modified_image, diff_img, ...
                                    sprintf('result/steganography_%s.png', pattern));
        
        % 保存修改后的图像
        imwrite(modified_image, sprintf('result/modified_lsb_%s.jpg', pattern));
        
        % 输出统计信息
        fprintf('均方误差 (MSE): %.6f\n', mse);
        fprintf('最大差异: %d\n', max_diff);
        modified_ratio = sum(diff_img(:) > 0) / numel(diff_img) * 100;
        fprintf('修改的像素比例: %.2f%%\n', modified_ratio);
    end
    
    % 保存原始图像和各个位平面
    imwrite(original_image, 'result/original_image.jpg');
    save_individual_bit_planes(bit_planes);
    
    % 输出详细的统计分析
    fprintf('\n=== 位平面分析结果统计 ===\n');
    fprintf('原始图像灰度范围: [%d, %d]\n', min(original_image(:)), max(original_image(:)));
    fprintf('原始图像平均灰度: %.2f\n', mean(original_image(:)));
    fprintf('原始图像标准差: %.2f\n', std(double(original_image(:))));
    
    % 分析各位平面的重要性（统计1的比例）
    fprintf('\n=== 各位平面重要性分析 ===\n');
    for i = 1:length(bit_planes)
        plane = bit_planes{i};
        bit_ratio = sum(plane(:) > 0) / numel(plane) * 100;
        if i == 1
            suffix = '(LSB)';
        elseif i == 8
            suffix = '(MSB)';
        else
            suffix = '    ';
        end
        fprintf('第%d位平面 %s: %.2f%% 的像素为1\n', i-1, suffix, bit_ratio);
    end
    
    % 输出保存的文件列表
    fprintf('\n=== 保存的文件 ===\n');
    fprintf('图像文件:\n');
    fprintf('- result/original_image.jpg (原始图像)\n');
    for i = 1:8
        fprintf('- result/bit_plane_%d.jpg (第%d位平面)\n', i-1, i-1);
    end
    for i = 1:length(modification_patterns)
        pattern = modification_patterns{i};
        fprintf('- result/modified_lsb_%s.jpg (修改最低位-%s)\n', pattern, pattern);
    end
    
    fprintf('图表文件:\n');
    fprintf('- result/bit_planes_all.png (所有位平面综合图)\n');
    for i = 1:length(modification_patterns)
        pattern = modification_patterns{i};
        fprintf('- result/steganography_%s.png (隐写对比-%s)\n', pattern, pattern);
    end
end

function bit_planes = extract_bit_planes(image)
% 提取图像的8个位平面
% 将每个像素的8位二进制表示分解为8个独立的位平面

    bit_planes = cell(8, 1);
    for i = 0:7
        % 右移i位后与1进行按位与操作，提取第i位
        bit_plane = bitand(bitshift(image, -i), 1);
        % 将0和1映射到0和255便于图像显示
        bit_plane = bit_plane * 255;
        bit_planes{i+1} = uint8(bit_plane);
    end
end

function modified_image = modify_lsb_plane(image, pattern)
% 修改最低位平面进行图像隐写实验
% 实现LSB(Least Significant Bit)隐写技术

    modified_image = image;
    [height, width] = size(image);
    
    switch pattern
        case 'random'
            % 模式1：随机置位，模拟随机信息隐藏
            random_bits = randi([0, 1], height, width, 'uint8');
            % 先清除原最低位(与0xFE按位与)，然后设置新的最低位
            modified_image = bitor(bitand(modified_image, 254), random_bits);
            
        case 'checkerboard'
            % 模式2：棋盘模式，测试规律性模式的影响
            checkerboard = zeros(height, width, 'uint8');
            checkerboard(1:2:end, 1:2:end) = 1;  % 偶数行偶数列设为1
            checkerboard(2:2:end, 2:2:end) = 1;  % 奇数行奇数列设为1
            modified_image = bitor(bitand(modified_image, 254), checkerboard);
            
        case 'zeros'
            % 模式3：全部置0，测试最小修改的影响
            modified_image = bitand(modified_image, 254);  % 清除最低位
            
        case 'ones'
            % 模式4：全部置1，测试最大修改的影响
            modified_image = bitor(modified_image, 1);  % 设置最低位为1
    end
end

function [diff, mse, max_diff] = calculate_difference(img1, img2)
% 计算两幅图像的差异指标
% 用于评估图像隐写的视觉影响

    % 计算像素级绝对差异
    diff = abs(double(img1) - double(img2));
    % 计算均方误差MSE
    mse = mean(diff(:) .^ 2);
    % 计算最大差异值
    max_diff = max(diff(:));
end

function show_bit_planes_individually(bit_planes)
% 单独显示每个位平面，便于观察细节
    for i = 1:length(bit_planes)
        fig = figure('Visible', 'off');  % 先创建不可见图形
        imshow(bit_planes{i});
        if i == 1
            title(sprintf('第%d位平面 (LSB)', i-1));
        elseif i == 8
            title(sprintf('第%d位平面 (MSB)', i-1));
        else
            title(sprintf('第%d位平面', i-1));
        end
        set(fig, 'Visible', 'on');  % 最后显示图形
    end
end

function plot_all_bit_planes(original_img, bit_planes, save_path)
% 绘制原图和所有位平面的综合显示
    fig = figure('Position', [100, 100, 1200, 1200], 'Visible', 'off');
    
    % 原始图像放在第一个位置
    subplot(3, 3, 1);
    imshow(original_img);
    title('原始图像');
    
    % 8个位平面按顺序排列
    positions = [2, 3, 4, 5, 6, 7, 8, 9];
    for i = 1:length(bit_planes)
        subplot(3, 3, positions(i));
        imshow(bit_planes{i});
        if i == 1
            title(sprintf('第%d位平面(LSB)', i-1));
        elseif i == 8
            title(sprintf('第%d位平面(MSB)', i-1));
        else
            title(sprintf('第%d位平面', i-1));
        end
    end
    
    % 保存综合位平面图
    if nargin > 2 && ~isempty(save_path)
        try
            saveas(fig, save_path);
            fprintf('位平面图已保存到: %s\n', save_path);
        catch ME
            fprintf('保存位平面图时出错: %s\n', ME.message);
        end
    end
    
    set(fig, 'Visible', 'on');  % 最后显示图形
end

function plot_steganography_comparison(original_img, modified_img, diff_img, save_path)
% 绘制图像隐写对比分析图
    fig = figure('Position', [100, 100, 1000, 800], 'Visible', 'off');
    
    % 子图1: 原始图像
    subplot(2, 2, 1);
    imshow(original_img);
    title('原始图像');
    
    % 子图2: 修改后图像
    subplot(2, 2, 2);
    imshow(modified_img);
    title('修改最低位后的图像');
    
    % 子图3: 差异图像（用热图显示）
    subplot(2, 2, 3);
    imshow(diff_img, []);
    colormap(jet);
    colorbar;
    title('差异图像');
    
    % 子图4: 差异值分布直方图
    subplot(2, 2, 4);
    histogram(diff_img(:), 50, 'FaceColor', 'red', 'FaceAlpha', 0.7);
    title('差异值分布');
    xlabel('差异值');
    ylabel('像素数量');
    grid on;
    
    % 先保存图形，再显示
    if nargin > 3 && ~isempty(save_path)
        try
            saveas(fig, save_path);
            fprintf('隐写对比图已保存到: %s\n', save_path);
        catch ME
            fprintf('保存隐写对比图时出错: %s\n', ME.message);
            % 尝试其他保存方法
            try
                print(fig, save_path, '-dpng', '-r300');
                fprintf('使用print函数成功保存: %s\n', save_path);
            catch
                fprintf('所有保存方法都失败了，继续执行...\n');
            end
        end
    end
    
    set(fig, 'Visible', 'on');  % 最后显示图形
end

function save_individual_bit_planes(bit_planes)
% 保存单独的位平面图像文件
    for i = 1:length(bit_planes)
        % 保存为JPEG格式便于查看
        imwrite(bit_planes{i}, sprintf('result/bit_plane_%d.jpg', i-1));
    end
end