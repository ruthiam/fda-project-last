import re

with open('Aviruth_HW1.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. ADD CVaR TO VaR CARD
var_card_pattern = re.compile(r'(<p class="text-2xl font-black text-white" id="varValue">--</p>\s*</div>)')
cvar_html = r'''\g<1>
                        <div class="mt-2 text-red-400 bg-red-900/20 p-2 rounded border border-red-500/20">
                            <h4 class="text-[10px] font-bold uppercase tracking-widest text-red-500/80 mb-1" title="Conditional Value at Risk (Expected Shortfall) measures average loss beyond VaR threshold.">Exp. Shortfall (CVaR)</h4>
                            <p class="text-lg font-bold" id="cvarValue">--</p>
                        </div>'''
text, n1 = var_card_pattern.subn(cvar_html, text)

# 2. ADD MDD & KUPIEC EXCEPTIONS TO VOLATILITY / CORRELATION CARD
# Actually let's put MDD inside Volatility Regime card or completely replace Correlation Card if not "All"
# Better: just add a new card! Let's find riskSummary grid
grid_pattern = re.compile(r'(<section id="riskSummary" class="grid grid-cols-1 md:grid-cols-)3')
text = grid_pattern.sub(r'\g<1>4', text) # Change to 4 columns!

mdd_html = r'''
                    <!-- MDD Card -->
                    <div class="glass-card p-6 rounded-2xl flex flex-col justify-between border-t-4 border-slate-500 transition-colors duration-300" id="mddStatusCard">
                        <div>
                            <h3 class="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Max Drawdown</h3>
                            <p class="text-2xl font-black text-white" id="mddValue">--</p>
                        </div>
                        <p class="text-[10px] text-slate-500 mt-4 uppercase">Peak-to-Trough Loss: <span id="mddStatusText" class="font-bold">Pending</span></p>
                    </div>
'''
# Insert MDD Card after volStatusCard
vol_card_end = re.compile(r'(<p class="text-\[10px\] text-slate-500 mt-4 uppercase">Status: <span id="volStatusText".*?</span>\s*</p>\s*</div>)')
text, n2 = vol_card_end.subn(r'\g<1>' + mdd_html, text)

# For Kupiec, let's put it in the VaR card footer
kupiec_pattern = re.compile(r'(What is the max predicted loss\?:.*?</span>\s*</p>)', re.DOTALL)
kupiec_html = r'''\g<1>
                        <p class="text-[10px] text-slate-500 mt-2 uppercase">Backtest Exceptions: <span id="kupiecText" class="font-bold text-white">--</span></p>'''
text, n3 = kupiec_pattern.subn(kupiec_html, text)


# 3. JS LOGIC FOR CVaR, MDD, Kupiec
js_logic_pattern = re.compile(r'(const zScoreVaR = Math\.abs\(\(var95_daily - meanRet\) / stdRet\);)')
js_addition = r'''\g<1>
                // 1b. CVaR (Expected Shortfall) Logic
                const tailReturns = sorted.filter(r => r <= var95_daily);
                let cvar_1day = 0;
                if(tailReturns.length > 0) {
                    cvar_1day = ss.mean(tailReturns);
                } else {
                    cvar_1day = var95_daily; // Fallback
                }
                const cvar_scaled = cvar_1day * timeScaler;
                const cvarElem = document.getElementById('cvarValue');
                if(cvarElem) cvarElem.textContent = (cvar_scaled * 100).toFixed(2) + "%";

                // 1c. Kupiec Backtest (Exception Counting)
                // How many days did the ACTUAL 1-day return drop below the 1-Day VaR threshold?
                const exceptions = allReturns.filter(r => r < var95_daily).length;
                const expectedExceptions = Math.round(allReturns.length * 0.05);
                const kupiecElem = document.getElementById('kupiecText');
                if(kupiecElem) kupiecElem.textContent = ${exceptions} (Expected: ~);
'''
text, n4 = js_logic_pattern.subn(js_addition, text)

# JS LOGIC for MDD
# Let's insert MDD at the bottom of updateRiskSummary
mdd_logic_target = r'corrStatusText\.className = "font-bold text-slate-500";\s*}'
mdd_logic_addition = r'''corrStatusText.className = "font-bold text-slate-500";
            }

            // 4. Max Drawdown (MDD) Logic
            const mddCard = document.getElementById('mddStatusCard');
            const mddValue = document.getElementById('mddValue');
            const mddStatusText = document.getElementById('mddStatusText');
            
            if (names.length > 0 && data[names[0]].prices.length > 0) {
                const prices = data[names[0]].prices;
                let maxDrawdown = 0;
                let peak = prices[0];
                
                for(let i=0; i < prices.length; i++) {
                    if (prices[i] > peak) {
                        peak = prices[i];
                    }
                    const drawdown = (prices[i] - peak) / peak;
                    if (drawdown < maxDrawdown) {
                        maxDrawdown = drawdown;
                    }
                }
                if(mddValue) mddValue.textContent = (maxDrawdown * 100).toFixed(2) + "%";
                
                if (mddCard && mddStatusText) {
                    if (maxDrawdown < -0.20) { // 20% crash
                        mddCard.className = "glass-card p-6 rounded-2xl flex flex-col justify-between border-t-4 border-[#ef4444] transition-colors duration-300";
                        mddStatusText.textContent = "Severe Bear Market";
                        mddStatusText.className = "font-bold text-[#ef4444]";
                    } else if (maxDrawdown < -0.10) { // 10% correction
                        mddCard.className = "glass-card p-6 rounded-2xl flex flex-col justify-between border-t-4 border-amber-500 transition-colors duration-300";
                        mddStatusText.textContent = "Market Correction";
                        mddStatusText.className = "font-bold text-amber-500";
                    } else {
                        mddCard.className = "glass-card p-6 rounded-2xl flex flex-col justify-between border-t-4 border-[#22c55e] transition-colors duration-300";
                        mddStatusText.textContent = "Normal Fluctuations";
                        mddStatusText.className = "font-bold text-[#22c55e]";
                    }
                }
            } else {
                if(mddValue) mddValue.textContent = "--";
                if(mddStatusText) mddStatusText.textContent = "N/A";
            }
'''
text, n5 = re.subn(mdd_logic_target, mdd_logic_addition, text)

with open('Aviruth_HW1.html', 'w', encoding='utf-8') as f:
    f.write(text)

print(f"Patches done: n1={n1}, n2={n2}, n3={n3}, n4={n4}, n5={n5}")
