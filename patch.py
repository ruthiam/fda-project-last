import re

with open('Aviruth_HW1.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update card html layout
html_old = '''                            <h3 class="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1"
                                title="Calculate the 95% Value at Risk using the Quantile Score method.">1-Day VaR Forecast
                            </h3>'''
html_new = '''                            <div class="flex items-center justify-between mb-1">
                                <h3 class="text-xs font-bold text-slate-400 uppercase tracking-widest"
                                    title="Calculate the 95% Value at Risk using the Quantile Score method.">VaR Forecast</h3>
                                <select id="varTimeframe" class="bg-slate-800 text-xs text-slate-300 border border-slate-600 rounded p-1 outline-none font-medium">
                                    <option value="1">1-Day</option>
                                    <option value="5">1-Week</option>
                                    <option value="21">1-Month</option>
                                    <option value="252">1-Year</option>
                                </select>
                            </div>'''

if html_old in content:
    content = content.replace(html_old, html_new)
else:
    print('Failed to find html_old')

# 2. Add event listener
js_old = "refreshBtn.addEventListener('click', () => updateDashboard());"
js_new = "refreshBtn.addEventListener('click', () => updateDashboard());\n        document.getElementById('varTimeframe').addEventListener('change', () => updateDashboard());"
if js_old in content:
    content = content.replace(js_old, js_new)
else:
    print('Failed to find js_old')

# 3. Modify VaR Logic
logic_old = '''            // 1. VaR Logic (Using the first selected asset or overall if "All")
            let allReturns = [];
            const names = mode === "All" ? Object.keys(data) : [mode];
            names.forEach(name => {
                allReturns = allReturns.concat(data[name].returns.filter(Number.isFinite).map(Number));
            });

            if (allReturns.length > 0) {
                const sorted = [...allReturns].sort((a, b) => a - b);
                const var95 = ss.quantileSorted(sorted, 0.05); // historical VaR at 95%
                varValue.textContent = (var95 * 100).toFixed(2) + "%";

                const meanRet = ss.mean(sorted);
                const stdRet = ss.standardDeviation(sorted);
                const zScoreVaR = Math.abs((var95 - meanRet) / stdRet);'''

logic_new = '''            const varTimeframeElem = document.getElementById('varTimeframe');
            const timeframeDays = varTimeframeElem ? parseInt(varTimeframeElem.value) : 1;
            const timeScaler = Math.sqrt(timeframeDays);

            // 1. VaR Logic (Using the first selected asset or overall if "All")
            let allReturns = [];
            const names = mode === "All" ? Object.keys(data) : [mode];
            names.forEach(name => {
                allReturns = allReturns.concat(data[name].returns.filter(Number.isFinite).map(Number));
            });

            if (allReturns.length > 0) {
                const sorted = [...allReturns].sort((a, b) => a - b);
                const var95_daily = ss.quantileSorted(sorted, 0.05); // historical VaR at 95%
                const var95_scaled = var95_daily * timeScaler;
                varValue.textContent = (var95_scaled * 100).toFixed(2) + "%";

                const meanRet = ss.mean(sorted);
                const stdRet = ss.standardDeviation(sorted);
                // Maintain z-score threshold logic based on daily metrics for statistical consistency
                const zScoreVaR = Math.abs((var95_daily - meanRet) / stdRet);'''

if logic_old in content:
    content = content.replace(logic_old, logic_new)
else:
    print('Failed to find logic_old')

# 4. Modify Status Text from 'tomorrow?:'
status_old = '''What is the max predicted loss for tomorrow?'''
status_new = '''What is the max predicted loss?'''
if status_old in content:
    content = content.replace(status_old, status_new)
else:
    print('Failed to find status_old')

with open('Aviruth_HW1.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done replacing.')
