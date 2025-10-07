from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import os
import time

# ==== Selenium初期化設定（ヘッドレス対応） ====
options = webdriver.ChromeOptions() 
options.add_argument("--headless")             # ブラウザ非表示
options.add_argument("--disable-gpu")          
options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

print("🌐 GooHome アパート・マンショントップページを開く...")
driver.get("") #対象の不動産URL
driver.implicitly_wait(3)

# 「借りる」＞「アパート・マンション」
driver.find_element(By.CLASS_NAME, "rent_aptmsn").click()

# 「沖縄県内の全市町村から探す」
driver.find_element(By.CSS_SELECTOR, "#all-area-search > ul > li:nth-child(1) > a").click()

# 「この条件で検索する」
driver.find_element(By.CSS_SELECTOR, "a.btn-w_cv.btnSearch").click()

# 「建物ごとに表示」
wait.until(EC.element_to_be_clickable((By.XPATH, "//li[text()='建物ごとに表示']"))).click()

# 表示件数を100に変更
pull_down_ini_100 = wait.until(EC.presence_of_element_located((By.NAME, "sort_count")))
Select(pull_down_ini_100).select_by_visible_text("100")

# =======================
# 物件リンクを取得（1ページ目）
# =======================
property_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//a[contains(text(),'詳細を見る')]")))
property_links = [item.get_attribute("href") for item in property_elements if item.get_attribute("href")]
print(f"取得リンク数: {len(property_links)} 件")

# =======================
# 出力設定
# =======================
columns = [
    "物件名","所在地","交通","階建","築年数","建物構造","設備","取引形態","取扱い不動産会社","詳細URL"
]
csv_file = "goohome_tab_scrape.xlsx"

data_list = []

# =======================
# 詳細ページ抽出処理
# =======================
for idx, link in enumerate(property_links, start=1):
    # 新しいタブで開く
    driver.execute_script("window.open(arguments[0]);", link)
    driver.switch_to.window(driver.window_handles[-1])

    try:
        # 各要素の抽出
        name = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="main_clm1"]/h2'))).text
        address = driver.find_element(By.XPATH, '//*[@id="detail_basic"]/div[2]/table[1]/tbody/tr[2]/td[1]').text
        traffic = driver.find_element(By.XPATH, '//*[@id="detail_basic"]/div[2]/table[1]/tbody/tr[2]/td[7]').text
        floors = driver.find_element(By.XPATH, '//*[@id="detail_pd"]/table[1]/tbody/tr[10]/td[2]').text
        age = driver.find_element(By.XPATH, '//*[@id="detail_pd"]/table[1]/tbody/tr[11]/td[1]').text
        structure = driver.find_element(By.XPATH, '//*[@id="detail_pd"]/table[2]/tbody/tr[3]/td[1]').text
        equipment = driver.find_element(By.XPATH, '//*[@id="detail_pd"]/table[2]/tbody/tr[2]/td').text
        transaction = driver.find_element(By.XPATH, '//*[@id="detail_pd"]/table[2]/tbody/tr[3]/td[2]').text
        company = driver.find_element(By.XPATH, '//*[@id="to-company"]/article/h3/a').text

        data_list.append([
            name, address, traffic, floors, age, structure, equipment, transaction, company, link
        ])
        print(f"{idx}/{len(property_links)} 件目取得完了: {name}")

    except Exception as e:
        print(f"⚠️ {idx} 件目でエラー: {e}")
    finally:
        # タブを閉じて元のタブに戻る
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    # 5件ごとに途中保存
    if idx % 5 == 0:
        df = pd.DataFrame(data_list, columns=columns)
        df.to_excel(csv_file, index=False)
        print(f"💾 {idx}件まで途中保存完了: {csv_file}")
        time.sleep(1)

# =======================
# 最終保存
# =======================
pd.DataFrame(data_list, columns=columns).to_excel(csv_file, index=False)
print(f"✅ 全{len(data_list)}件を {csv_file} に出力しました。")

driver.quit()
