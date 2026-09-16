# Sürekli öğrenme pilotu — kapatılmış araştırma arşivi

**16 Eylül 2026: Son v0.5 denemesi tamamlandı ve araştırma hattı kapatıldı.**

Bu depo, sentetik sürekli öğrenme deneylerinin tasarımını, keşifsel
pilotlarını, önkayıtlarını ve başarısız fizibilite kontrollerini korur.
Yönlendirme ve yenilemenin sürekli öğrenmede üstünlüğü gösterilmedi;
planlanan ana faktöriyel deney çalıştırılmadı.

## Son sonuç

- v0.4: 200 adaydan hiçbiri jeneratör kabulünü geçmedi.
- v0.5: marj eşiği 0,1 ile ilk beş adaydan üç jeneratör kabul edildi.
- İlk çiftin R1/M1 kontrolünde A temiz doğruluğu **%92,835**;
  Wilson %95 aralığı **[%92,4693; %93,1843]**.
  Gerekli eşik **%93,2525** olduğundan kapı geçilmedi.
- CPR hareketi ve B/D'nin tek-ağ referansına göre en fazla 2 puan
  kayıp kontrolleri geçti; bunlar öğrenilebilirlik başarısı değildir.
- R2/M2 eğitimi, kalan çiftler, temsil tanısı, süre/güç pilotları ve
  ana deney durma kuralı nedeniyle çalıştırılmadı.
- Başka eşik, havuz veya bilimsel revizyon denenmeyecek.

## Okuma sırası

1. [Nihai sonuçlar, tablolar ve öğrenilenler](continual_pilot/line2/FINAL_RESULTS_AND_LESSONS.md)
2. [v0.5 sonuç öncesi son deneme protokolü](continual_pilot/line2/PREREGISTRATION_V05_2026-09-16.md)
3. [v0.5 içerik kilidi](continual_pilot/line2/LOCK_V05_2026-09-16.md)
4. [113 mekanik testin kaynağa bağlı kanıtı](continual_pilot/line2/validation_v05_2026-09-16_01.json)
5. [Tarihsel araştırma günlüğü](continual_pilot/README.md)

**Gelecek iş — uygulanmayan kapsam:** [kilitli kapsamlı protokolün](continual_pilot/line2/PREREGISTRATION_DRAFT.md)
süre doğrulaması, güç pilotu ve ana deney bölümleri.
Bu etiket yeni çalışma izni veya devam taahhüdü değildir.

## Kayıtlar ve sınırlamalar

[Ham arşivler sürüm eklerinde](https://github.com/FearmessOp/continual-pilot/releases)
tutulur; büyük ham veri arşivleri Git geçmişine eklenmez.
[v0.4 dış yedeği](continual_pilot/line2/BACKUP_V04_VERIFICATION_2026-09-16.json),
geri indirilen 11 parçadaki manifest dahil 3.651 dosyayla doğrulandı.

[Özgün protokolün Bitcoin tasdiki](continual_pilot/line2/OTS_VERIFICATION_2026-09-16.json),
967295 numaralı blokta Merkle/başlık/iş ispatı kontrolleri ve iki HTTPS
gezginiyle doğrulandı. Yerel tam zincir doğrulaması değildir;
bu tasdik v0.5 belgesinin zaman damgası olarak sunulmaz.

Eski günlüklerdeki “güncel”, “sonraki adım” ve çalıştırma talimatları
tarihsel bağlamlarına aittir. Eski güçlü nedensel yorumlar nihai yazının
sınırlamalarıyla okunmalıdır. Mekanik test başarısı bilimsel başarı değildir.

Çalışmalar CPU üzerinde Python, NumPy ve PyTorch ile gerçekleştirildi.
Kesin sürümler, tohumlar ve kaynak özetleri koşu kayıtlarında bulunur.
Tarihsel komutları çalıştırmak bazı eski sonuçların üzerine yazabilir;
arşiv kayıtları değişmeden korunmalıdır.

Lisans: [MIT](LICENSE).