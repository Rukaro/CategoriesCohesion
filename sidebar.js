// 飞书 SDK 初始化
// 参考 @lark-base-open/js-sdk 和飞书官方文档
// 在飞书环境中，SDK 会自动注入到 window.bitable
// 直接使用 window.bitable，不需要局部变量

// 检查是否在飞书环境中
function isInFeishuEnvironment() {
    // 方法1: 检查 User-Agent
    const ua = navigator.userAgent || '';
    const isFeishuUA = /Feishu|Lark/i.test(ua);
    
    // 方法2: 检查 URL 域名（更可靠）
    const hostname = window.location.hostname || '';
    const isFeishuDomain = /feishu\.cn|larkoffice\.com|bytedance\.com/i.test(hostname);
    
    // 方法3: 检查 SDK 是否已存在
    const hasBitable = typeof window.bitable !== 'undefined';
    
    // 方法4: 检查父窗口（如果在 iframe 中）
    let isInFeishuFrame = false;
    try {
        if (window.parent !== window) {
            const parentHostname = window.parent.location?.hostname || '';
            isInFeishuFrame = /feishu\.cn|larkoffice\.com|bytedance\.com/i.test(parentHostname);
        }
    } catch (e) {
        // 跨域限制，无法访问父窗口
    }
    
    const result = isFeishuUA || isFeishuDomain || hasBitable || isInFeishuFrame;
    
    console.log('环境检测结果:', {
        userAgent: isFeishuUA,
        domain: isFeishuDomain,
        hostname: hostname,
        hasBitable: hasBitable,
        parentFrame: isInFeishuFrame,
        result: result
    });
    
    return result;
}

// 等待飞书 SDK 可用
// 参考 text-generator 项目，SDK 可以通过 npm 包或自动注入
async function waitForBitable() {
    // 如果 SDK 已经可用，直接返回
    if (typeof window.bitable !== 'undefined' && window.bitable.base) {
        console.log('✓ 飞书 SDK 已就绪');
        return;
    }
    
    // 检查环境（但不强制要求，因为 SDK 可能通过 CDN 加载）
    const inFeishuEnv = isInFeishuEnvironment();
    if (inFeishuEnv) {
        console.log('✓ 检测到在飞书环境中，等待 SDK 自动注入...');
    } else {
        console.log('不在飞书环境中，等待 SDK 从 CDN 加载...');
    }
    
    console.log('当前 URL:', window.location.href);
    
    // 等待 SDK 加载（无论是自动注入还是 CDN 加载）
    return new Promise((resolve, reject) => {
        let attempts = 0;
        const maxAttempts = 300; // 30秒
        
        const checkSDK = setInterval(() => {
            attempts++;
            
            if (typeof window.bitable !== 'undefined' && window.bitable.base) {
                clearInterval(checkSDK);
                console.log('✓ 飞书 SDK 加载成功');
                resolve();
                return;
            }
            
            // 每2秒输出一次等待信息
            if (attempts % 20 === 0) {
                console.log(`等待 SDK 注入中... (${attempts * 0.1}秒)`);
            }
            
            // 超时处理
            if (attempts >= maxAttempts) {
                clearInterval(checkSDK);
                
                // 检查是否在 wiki 页面
                const isWikiPage = /wiki|docx/i.test(window.location.href);
                const isTablePage = /table|bitable/i.test(window.location.href);
                
                let errorMsg = '飞书 SDK 加载超时。\n\n';
                errorMsg += '可能的原因：\n';
                errorMsg += '1. 网络问题导致 SDK 无法加载\n';
                errorMsg += '2. 在 Wiki 页面中，bitable SDK 可能不可用\n';
                errorMsg += '3. 需要在多维表格中使用插件\n\n';
                
                if (isWikiPage && !isTablePage) {
                    errorMsg += '⚠️ 检测到在飞书 Wiki 页面中。\n\n';
                    errorMsg += '建议：在多维表格中打开插件以获得完整功能。\n\n';
                }
                
                errorMsg += '请尝试：\n';
                errorMsg += '1. 刷新页面\n';
                errorMsg += '2. 检查网络连接\n';
                errorMsg += '3. 在多维表格中打开插件（而不是 Wiki 页面）\n';
                errorMsg += '4. 查看浏览器控制台的详细错误信息';
                
                console.error('=== SDK 加载失败 ===');
                console.error(errorMsg);
                console.error('调试信息:', {
                    url: window.location.href,
                    hostname: window.location.hostname,
                    userAgent: navigator.userAgent,
                    hasBitable: typeof window.bitable !== 'undefined',
                    bitableType: typeof window.bitable,
                    isWiki: isWikiPage,
                    isTable: isTablePage
                });
                reject(new Error(errorMsg));
            }
        }, 100);
    });
}

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
    try {
        console.log('开始初始化插件...');
        
        // 等待飞书 SDK 加载完成
        await waitForBitable();

        // 加载字段列表
        await loadFields();

        // 绑定事件
        document.getElementById('analyze-btn').addEventListener('click', handleAnalyze);
        document.getElementById('refresh-btn').addEventListener('click', loadFields);

        // 监听字段选择变化
        document.getElementById('category-field').addEventListener('change', checkFields);
        document.getElementById('items-field').addEventListener('change', checkFields);

        console.log('插件初始化完成');
    } catch (error) {
        showError('初始化失败: ' + error.message);
        console.error('初始化错误:', error);
        console.error('调试信息:', {
            windowBitable: typeof window.bitable,
            hasBase: window.bitable?.base ? '存在' : '不存在',
            userAgent: navigator.userAgent
        });
    }
});

// 加载字段列表
async function loadFields() {
    try {
        // 直接使用 window.bitable，参考官方文档
        if (typeof window.bitable === 'undefined' || !window.bitable.base) {
            throw new Error('飞书 SDK 未正确初始化');
        }
        
        const table = await window.bitable.base.getActiveTable();
        const fieldList = await table.getFieldList();

        const categorySelect = document.getElementById('category-field');
        const itemsSelect = document.getElementById('items-field');

        // 清空选项
        categorySelect.innerHTML = '<option value="">请选择字段</option>';
        itemsSelect.innerHTML = '<option value="">请选择字段</option>';

        // 填充字段选项（只显示文本类型字段）
        // 字段类型：1=文本, 2=数字, 3=单选, 4=多选, 5=日期, 6=复选框, 7=人员, 8=电话, 9=邮箱, 10=超链接, 11=附件, 13=关联, 15=公式, 17=双向关联, 18=地理位置, 19=群组, 20=创建时间, 21=最后更新时间, 22=创建人, 23=修改人, 1001=自动编号, 1002=条码, 1003=按钮
        for (const field of fieldList) {
            const fieldType = await field.getType();
            // 支持文本类型字段（类型1）
            if (fieldType === 1) {
                const fieldName = await field.getName();
                const fieldId = field.id;

                const option1 = document.createElement('option');
                option1.value = fieldId;
                option1.textContent = fieldName;
                categorySelect.appendChild(option1);

                const option2 = document.createElement('option');
                option2.value = fieldId;
                option2.textContent = fieldName;
                itemsSelect.appendChild(option2);
            }
        }

        checkFields();
    } catch (error) {
        showError('加载字段失败: ' + error.message);
        console.error('加载字段错误:', error);
    }
}

// 检查字段是否已选择
function checkFields() {
    const categoryField = document.getElementById('category-field').value;
    const itemsField = document.getElementById('items-field').value;
    const analyzeBtn = document.getElementById('analyze-btn');

    analyzeBtn.disabled = !(categoryField && itemsField && categoryField !== itemsField);
}

// 处理分析请求
async function handleAnalyze() {
    try {
        // 检查 SDK 是否可用，直接使用 window.bitable
        if (typeof window.bitable === 'undefined' || !window.bitable.base) {
            throw new Error('飞书 SDK 未正确初始化，请刷新页面重试');
        }
        
        // 隐藏结果和错误
        document.getElementById('result-section').style.display = 'none';
        document.getElementById('error-section').style.display = 'none';
        document.getElementById('loading-section').style.display = 'block';

        // 获取选中的记录，使用 window.bitable
        const table = await window.bitable.base.getActiveTable();
        const selection = await window.bitable.base.getSelection();
        
        if (!selection || !selection.recordIds || selection.recordIds.length === 0) {
            throw new Error('请先选中一条记录');
        }

        const recordId = selection.recordIds[0];
        const record = await table.getRecordById(recordId);

        // 获取字段值
        const categoryFieldId = document.getElementById('category-field').value;
        const itemsFieldId = document.getElementById('items-field').value;
        const aggregationMethod = document.getElementById('aggregation-method').value;

        if (!categoryFieldId || !itemsFieldId) {
            throw new Error('请先选择类目词和普通词字段');
        }

        // 获取字段值（文本类型字段的值格式为数组，包含对象，对象有text属性）
        const categoryValue = record.fields[categoryFieldId];
        const itemsValue = record.fields[itemsFieldId];

        // 验证数据
        let category = '';
        if (categoryValue && Array.isArray(categoryValue) && categoryValue.length > 0) {
            category = categoryValue[0].text ? categoryValue[0].text.trim() : String(categoryValue[0]).trim();
        } else if (categoryValue) {
            category = String(categoryValue).trim();
        }

        if (!category) {
            throw new Error('类目词字段为空或格式不正确');
        }

        let itemsText = '';
        if (itemsValue && Array.isArray(itemsValue) && itemsValue.length > 0) {
            itemsText = itemsValue[0].text ? itemsValue[0].text.trim() : String(itemsValue[0]).trim();
        } else if (itemsValue) {
            itemsText = String(itemsValue).trim();
        }

        if (!itemsText) {
            throw new Error('普通词字段为空或格式不正确');
        }

        // 解析普通词（假设用换行、逗号或分号分隔）
        const items = itemsText
            .split(/[\n,;，；]/)
            .map(item => item.trim())
            .filter(item => item.length > 0);

        if (items.length === 0) {
            throw new Error('普通词字段中没有有效的词语');
        }

        // 调用后端 API 进行计算
        const response = await fetch('http://localhost:5000/api/calculate-cohesion', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                category: category,
                items: items,
                aggregation_method: aggregationMethod
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || '计算失败');
        }

        const result = await response.json();

        // 显示结果
        displayResult(result, category, items, aggregationMethod);

    } catch (error) {
        showError(error.message);
    } finally {
        document.getElementById('loading-section').style.display = 'none';
    }
}

// 显示结果
function displayResult(result, category, items, method) {
    const resultSection = document.getElementById('result-section');
    const cohesionScore = document.getElementById('cohesion-score');
    const categoryText = document.getElementById('category-text');
    const itemsCount = document.getElementById('items-count');
    const methodText = document.getElementById('method-text');
    const similarityList = document.getElementById('similarity-list');

    // 设置主要结果
    cohesionScore.textContent = result.cohesion_score.toFixed(4);
    categoryText.textContent = category;
    itemsCount.textContent = items.length;
    methodText.textContent = method === 'mean' ? '平均值 (Mean)' : '中位数 (Median)';

    // 显示相似度详情
    similarityList.innerHTML = '';
    result.similarities.forEach((sim, index) => {
        const item = document.createElement('div');
        item.className = 'similarity-item';
        item.innerHTML = `
            <span class="similarity-item-text">${items[index]}</span>
            <span class="similarity-item-score">${sim.toFixed(4)}</span>
        `;
        similarityList.appendChild(item);
    });

    resultSection.style.display = 'block';
}

// 显示错误
function showError(message) {
    const errorSection = document.getElementById('error-section');
    const errorMessage = document.getElementById('error-message');
    errorMessage.textContent = message;
    errorSection.style.display = 'block';
}

