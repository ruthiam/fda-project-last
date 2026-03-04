import re

with open('Aviruth_HW1.html', 'r', encoding='utf-8') as f:
    text = f.read()

# HTML patch
p1 = re.compile(r'<h3[^>]+1-Day VaR\s*Forecast\s*</h3>', re.IGNORECASE)
r1 = r'''<div class="flex items-center justify-between mb-1">
                                <h3 class="text-xs font-bold text-slate-400 uppercase tracking-widest"
                                    title="Calculate the 95% Value at Risk using the Quantile Score method.">VaR Forecast</h3>
                                <select id="varTimeframe" class="bg-slate-800 text-xs text-slate-300 border border-slate-600 rounded p-1 outline-none font-medium">
                                    <option value="1">1-Day</option>
                                    <option value="5">1-Week</option>
                                    <option value="21">1-Month</option>
                                    <option value="252">1-Year</option>
                                </select>
                            </div>'''
text, n1 = p1.subn(r1, text)
print(f'HTML patch: {n1}')

# JS Listeners
p2 = re.compile(r"refreshBtn\.addEventListener\('click',\s*\(\)\s*=>\s*updateDashboard\(\)\);")
r2 = "refreshBtn.addEventListener('click', () => updateDashboard());\n        document.getElementById('varTimeframe').addEventListener('change', () => updateDashboard());"
text, n2 = p2.subn(r2, text)
print(f'JS Listeners patch: {n2}')

# Status text
p3 = re.compile(r"What is the max predicted loss for tomorrow\?:")
r3 = "What is the max predicted loss?:"
text, n3 = p3.subn(r3, text)
print(f'Status text patch: {n3}')

# Logic
p4 = re.compile(r"// 1\. VaR Logic.*?const zScoreVaR = Math\.abs\(\(var95 - meanRet\) / stdRet\);", re.DOTALL)
r4 = r"""const varTimeframeElem = document.getElementById('varTimeframe');
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
                const zScoreVaR = Math.abs((var95_daily - meanRet) / stdRet);"""
text, n4 = p4.subn(r4, text)
print(f'Logic patch: {n4}')

with open('Aviruth_HW1.html', 'w', encoding='utf-8') as f:
    f.write(text)

