# coding=utf-8
import sys

def patch_chart():
    with open("app/dashboard.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        if 'if view_mode ==' in line and '차트' in line:
            # Found the start of chart view block.
            # Insert the aggregation logic right after importing go
            for j in range(i, i+15):
                if 'import plotly.graph_objects as go' in lines[j]:
                    insert_idx = j + 1
                    
                    agg_code = """
            # 차트뷰에서는 같은 가격대의 수량을 합산하여 깔끔하게 표시
            chart_sell_df = sell_df.groupby("avg_price", as_index=False)["quantity"].sum() if not sell_df.empty else sell_df
            chart_buy_df  = buy_df.groupby("avg_price", as_index=False)["quantity"].sum() if not buy_df.empty else buy_df
"""
                    lines.insert(insert_idx, agg_code)
                    break
            
            # Now we need to replace `sell_df.iterrows()` with `chart_sell_df.iterrows()`
            # and `buy_df.iterrows()` with `chart_buy_df.iterrows()` inside the chart block
            for k in range(insert_idx, insert_idx+50):
                if 'for _, row in sell_df.iterrows():' in lines[k]:
                    lines[k] = lines[k].replace('sell_df', 'chart_sell_df')
                if 'for _, row in buy_df.iterrows():' in lines[k]:
                    lines[k] = lines[k].replace('buy_df', 'chart_buy_df')
            
            break

    with open("app/dashboard.py", "w", encoding="utf-8") as f:
        f.writelines(lines)

if __name__ == "__main__":
    patch_chart()

