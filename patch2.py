import re

with open('Aviruth_HW1.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update card html layout
pattern = r'(<h3[^>]*>)\s*1-Day VaR Forecast\s*(</h3>)'
replacement = r'''<div class="flex items-center justify-between mb-1">
                          \g<1>VaR Forecast\g<2>
                          <select id="varTimeframe" class="bg-slate-800 text-xs text-slate-300 border border-slate-600 rounded p-1 outline-none font-medium">
                              <option value="1">1-Day</option>
                              <option value="5">1-Week</option>
                              <option value="21">1-Month</option>
                              <option value="252">1-Year</option>
                          </select>
                      </div>'''

text, n = re.subn(pattern, replacement, text)
print(f'HTML patch applied {n} times.')

# 4. Modify 'tomorrow?:'
pattern2 = r'What is the max predicted loss for tomorrow\?:'
replacement2 = r'What is the max predicted loss?:'
text, n2 = re.subn(pattern2, replacement2, text)
print(f'Status patch applied {n2} times.')

with open('Aviruth_HW1.html', 'w', encoding='utf-8') as f:
    f.write(text)

