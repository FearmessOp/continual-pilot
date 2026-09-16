# Nihai durum — araştırma hattı kapatıldı (2026-09-16)

**v0.5 son denemesi tamamlandı. Yeni eşik, havuz, bilimsel revizyon veya
eğitim koşusu planlanmıyor.**

[Sonuç ve öğrenilenler](line2/FINAL_RESULTS_AND_LESSONS.md),
[son deneme önkaydı](line2/PREREGISTRATION_V05_2026-09-16.md) ve
[içerik kilidi](line2/LOCK_V05_2026-09-16.md).

- Jeneratör kabulü: ilk beş adaydan 11002, 11003 ve 11004 kabul edildi.
- İlk çiftin R1/M1 kapısında A: %92,835 temiz doğruluk;
  Wilson %95 aralığı [%92,469272; %93,184276], gerekli eşik %93,2525.
  Kapı geçilmedi.
- C ve CPR'li uzman-1 referansı da öğrenilebilirlik kapısını geçemedi.
  CPR hareket kontrolü ve B/D'nin tek-ağ referansına göre en fazla
  2 puan kayıp kontrolü geçti; bunlar mutlak öğrenilebilirlik başarısı değildir.
- R2/M2 kontrol eğitimi, diğer çiftler, temsil tanısı, süre/güç pilotları
  ve ana deney başlatılmadı.
- 113 mekanik testin başarısı, bilimsel kapının geçtiği anlamına gelmez.
- [v0.4 ham dış yedeği](line2/BACKUP_V04_VERIFICATION_2026-09-16.json)
  GitHub sürüm eklerinden geri indirilerek manifestle doğrulandı.
- [Özgün protokolün Bitcoin tasdiki](line2/OTS_VERIFICATION_2026-09-16.json)
  Merkle/başlık/iş ispatı ve iki gezgin üzerinden doğrulandı;
  yerel tam zincir doğrulaması değildir ve v0.5 belgesini damgalamaz.

**Gelecek iş — uygulanmayan kapsam:** [kilitli kapsamlı protokolün](line2/PREREGISTRATION_DRAFT.md)
filtreli süre doğrulaması, güç pilotu ve ana faktöriyel deneyi.
Bu etiket devam izni veya taahhüdü değildir; özgün kilitli belge korunur.

## Aşağıdaki metin tarihsel araştırma günlüğüdür

Aşağıdaki “güncel durum”, “sonraki adım” ve çalıştırma ifadeleri yazıldıkları
tura aittir; yukarıdaki nihai kapanışın yerine geçmez. Eski kesin neden,
tam unutma, imkânsızlık ve tarihsel tahmin eşitliği yorumları
[nihai yazıdaki sınırlamalarla](line2/FINAL_RESULTS_AND_LESSONS.md) okunmalıdır.
Tarihsel komutlar bu kapanış kapsamında yeni deney izni değildir.

---

# Sürekli öğrenme — en küçük CPU pilotu

## Güncel durum — kısaltılmış pilotta 1.024 örnek seçildi

**Keşiften türetilmiş pilot; öğrenilebilirlik kapısı geçilmedi.**

[Sonuç öncesi protokol](short_pilot/PROTOCOL.md),
[ayrıntılı sonuç tabloları](short_pilot/RESULTS.md),
[tam sayısal rapor](short_pilot/results/summary.json) ve
[kayıt bütünlüğü manifesti](short_pilot/results/manifest.json).

Yeni 240001–240003 akışlarında faz uzunlukları
40.000 → 10.000 → (1.024 / 1.536) → 4.000 olarak sınandı.
A'nın faz-2 R1 doğrulukları %86,400 / %86,610 / %87,160 ile
bu turun en az %86 başlangıç kontrolünü sağladı.
Önceki pilotun kontrolü %80 idi; %86 bu yeni protokolün değişikliğidir.

| Akış | A hasarı: 1.024 örnek (puan) | A hasarı: 1.536 örnek (puan) |
|---|---:|---:|
| 240001 | 24,870 | 32,970 |
| 240002 | 26,190 | 35,890 |
| 240003 | 28,500 | 34,555 |

İki aday da üç akışın tümünde 20–40 yüzde puanı bandını sağladı.
Önceden yazılan en kısa uygun aday kuralıyla **1.024 örnek / 64 güncelleme**
seçildi. 1.536 örnek / 96 güncelleme de uygundu.
1.792/768 sonraki-aday dalları tetiklenmedi ve çalıştırılmadı.

Seçilen adayda D480, A için 107 / 101 / 129; replay için 19 / 12 / 16.
Her pencere 480 örnek ve tam 30 güncellemedir.
Ancak faz-3 sonu R2 doğruluğu A'da %63,060–%64,445,
replay'de %43,020–%44,145 olduğundan düşük D480 tek başına üstünlük değildir.
Faz-4 sonu R1 doğrulukları da sırasıyla %86,380–%87,225 ve
%80,905–%82,050 olarak birlikte raporlandı.

Hat 2 için yeni-kural öğrenimi ve eski-kural performansının çift ölçü
olarak raporlanması, tek D480 ile kazanan ilan edilmemesi ve 64 adımda
mekanizma tepkisizliğinin olası sonuç olarak korunması protokole yazıldı.
Yeni karar ağacının 9 testi ve ortak eğitim çekirdeğinin 8 testi geçti.
Kontrol noktaları, optimizer/tampon/RNG durumları, girdiler, hedefler,
tahminler ve koşu öncesi kaynak kopyaları doğrulanarak saklandı.

**Bu seçim yalnızca v0.3 pilotuna aittir; filtreli v0.4'e otomatik
aktarılmaz. Hat 2, v0.4 ve yeni mekanizmalar bu turda çalıştırılmadı.**
Aşağıdaki önceki pilot sonuçları tarihsel kayıt olarak korunmaktadır.

---

## Güncel durum — asimetrik faz uzunluğu pilotu

**Keşiften türetilmiş pilot; öğrenilebilirlik kapısı geçilmedi.**

[Sonuç öncesi protokol](asymmetric_pilot/PROTOCOL.md),
[ayrıntılı sonuç tabloları](asymmetric_pilot/RESULTS.md),
[tam sayısal rapor](asymmetric_pilot/results/summary.json) ve
[kayıt bütünlüğü manifesti](asymmetric_pilot/results/manifest.json).

40.000 → 10.000 → (2.000 veya 4.000) → 4.000 örneklik asimetrik düzen,
önceki keşiften ayrı üç akışta A ve replay ile sınandı.
Her yöntemin iki süre adayı aynı faz-2 model, optimizer, tampon ve RNG
durumundan dallandı. Yeni pilotun 8 ilgili testi geçti.

**Aday seçilmedi.** A'nın 2.000 örneklik faz-3 hasarı üç akışta
37,825 / 38,160 / 40,550 yüzde puanı; 4.000 örneklik adayda
41,875 / 43,550 / 42,925 puan oldu. Önceden sabitlenen 20–40 puan
bandını üç akışın tümünde sağlayan aday yok. Üçüncü akışın 0,550 puanlık
taşması yuvarlanarak kabul edilmedi; bant genişletilmedi.
A'nın faz-2 R1 doğrulukları %86,540–%87,170 ile pilotun %80 başlangıç
öğrenimi kontrolünü sağladı; bu kontrol öğrenilebilirlik kapısı değildir.

Faz 3 adayları 125/250 güncelleme içerdi. Faz 4'ün ilk 480 örneğinde
tam 30 güncelleme ölçüldü; D480 ve D480/480, donmuş R1/R2 doğrulukları,
hasar/toparlanma ve faz başına toplam/örnek başına kâhin pişmanlığı
ayrıntılı sonuçlarda raporlandı. Girdiler ve hedefler dahil kalıcı kayıtlar,
kontrol noktaları ve koşu öncesi kaynak kopyaları ayrı dizinde saklandı.

Bu sonuç kısa fazların imkânsızlığını göstermez; sınanan iki adayın
belirlenen seçim kuralını sağlamadığını gösterir.
**Hat 2'ye aktarılacak süre sabitlenmedi; v0.4, k-NN, CPR ve yönlendirme
bu turda çalıştırılmadı.** Önceki “tam üzerine yazma” ve “etkileşim
ölçülemez” ifadeleri kesin kanıt olarak okunmamalıdır: öğretmen uyumuna
yakın doğruluk tam bilgi kaybını, olası taban etkisi de etkileşimin
zorunlu olarak sıfıra çökmesini kanıtlamaz.

---

## Hat 1 faz-3 eğrileri: unutma ~2.000 örnekte tamamlanıyor

**Öğrenilebilirlik kapısı geçilmedi; keşif, hipotez testi değil.** Uygulama:
[`curves_v03.py`](curves_v03.py); testler: [`test_curves_v03.py`](test_curves_v03.py);
tam eğriler: [`results_curves_v03/summary.json`](results_curves_v03/summary.json).
Yeni eğitim yok; eğriler kayıtlı tahminlerden çıkarıldı. Faz pişmanlığı
eşleşmesi üç tohumda da tuttu (akış doğru yeniden üretildi). **75 test geçti.**

### Öğretmen uyumu ölçüldü

M2 altında R1–R2 öğretmen uyumu üç tohumda **%40,9–%41,4** (uyuşmazlık
%58,6–%59,1). Bu, A'nın faz-3 tabanının neden ~%42 olduğunu açıklar: model
tümüyle R2'ye döndüğünde R1 etiketlerine karşı doğruluğu, iki kuralın
çakıştığı örneklerin oranına (uyum) iner.

### A'nın R1 unutma eğrisi (1.000 blok, tohum 220001 örnek)

| Blok sonu | 1.000 | 2.000 | 3.000 | 5.000 | 10.000 | 40.000 |
|---|---:|---:|---:|---:|---:|---:|
| A pred–R1 | %71,1 | %51,2 | %46,1 | %50,5 | %45,5 | %41,9 |
| A pred–R2 | %51,9 | %69,2 | %72,2 | %78,5 | %81,9 | %83,4 |

Unutma **2.000 örnekte büyük ölçüde tamamlanıyor**: R1 doğruluğu ilk blokta
faz-2 tavanının (~%89) altına, ikinci blokta ~%50'ye, üçüncüden itibaren
uyum tabanına (~%41) oturuyor. R2 doğruluğu aynı anda hızla yükseliyor —
bu tam üzerine yazmadır; kısmi bozulma değil.

### Replay'in R2 uyum eğrisi çok yavaş

| Blok sonu | 1.000 | 5.000 | 10.000 | 20.000 | 40.000 |
|---|---:|---:|---:|---:|---:|
| replay pred–R2 | %41,4 | %47,8 | %48,8 | %50,7 | %55,8 |
| replay pred–R1 | %81,2 | %82,9 | %79,5 | %76,6 | %69,7 |

Replay R1'i ~%70–85'te korurken R2'yi **40.000 örnekte bile ancak ~%56'ya**
çıkarabiliyor; hiçbir blokta %60'ı geçmiyor. Bu, replay'in faz-3 pişmanlığının
neden A'nın iki katı olduğunu doğrudan gösterir: tampondaki R1 örnekleri,
aynı M2 girdilerine çelişen etiketle eğitim yaptırıp R2 uyumunu bloke ediyor.

### Faz uzunluğu için taban etkisi doğrulandı; aday pencere

40.000/faz, A'nın unutma tabanına oturmasından çok sonrasını ölçüyor.
Etkileşim ölçümü \(I=(E_D-E_B)-(E_C-E_A)\) için A korumada tabanda
olduğundan \(E_C-E_A\) sıkışır ve I fiilen \(E_D-E_B\)'ye çöker; mevcut
uzunlukta yenileme×yönlendirme etkileşimi ölçülemez. Aday hasar penceresi
(R1 doğruluğu faz-2'den 20–40 puan düşük, yani ~%49–69) üç tohumda ortak
olarak **blok 2.000** civarındadır (220001'de 2.000/4.000/5.000, 220002'de
2.000/4.000, 220003'te 2.000). Bu, faz uzunluğunun **birkaç binlik** ölçekte
sınanması gerektiğini düşündürür.

**Sınırlar:** Bunlar çevrimiçi blok doğruluklarıdır, dondurulmuş kontrol
noktası değil; erken bloklar R2 öğrenmesiyle örtüşür. Aday aralık kesin
değildir; ayrı bir faz-uzunluğu pilotunda dondurulmuş ölçümle doğrulanmalı
ve önkayıta öyle girmelidir. Tampondaki R1 oranı faz 3 boyunca sabit değil
(~%100 → ~%66,7); çelişen-etiket açıklaması güçlü adaydır, kanıtlanmış
mekanizma değildir. 40.000 Hat 2'ye taşınmaz; faz uzunluğu bu aday
aralıktan ayrı pilotla sabitlenir.

---

## Hat 1 keşif sonucu: unutma büyük ve görünür; replay dengeyi kaydırıyor

**Öğrenilebilirlik kapısı geçilmedi; bu koşu hipotez testi değil, etki
penceresi keşfidir.** Uygulama: [`impact_v03.py`](impact_v03.py); testler:
[`test_impact_v03.py`](test_impact_v03.py); tam sonuç:
[`results_impact_v03/summary.json`](results_impact_v03/summary.json); kalıcı
model ve tahmin kayıtları: [`results_impact_v03/records/`](results_impact_v03/records).

**70 yazılım testi geçti.** Jeneratör 1000 sabit; üç eğitim/akış tohumu
(220001–220003). A ve replay her tohumda aynı başlangıç ağırlığının deepcopy
kopyasını (özet 57cf93…) ve aynı akışı aldı. Faz 2/3/4 donmuş kopyaları
aynı bağımsız M2/R1 akışında (20.000 örnek) değerlendirildi.

### Donmuş M2/R1 doğrulukları ve geçiş bedeli

| Tohum | Yöntem | Faz2 | Faz3 | Faz4 | Hasar (2→3) | Toparlanma (3→4) | D₁₀₀₀ |
|---|---|---:|---:|---:|---:|---:|---:|
| 220001 | A | %88,98 | %43,30 | %89,95 | %45,69 | %46,65 | 310 |
| 220001 | replay | %84,83 | %68,73 | %79,62 | %16,09 | %10,89 | 107 |
| 220002 | A | %88,79 | %41,63 | %90,17 | %47,16 | %48,54 | 328 |
| 220002 | replay | %86,67 | %70,31 | %77,71 | %16,36 | %7,40 | 150 |
| 220003 | A | %89,07 | %43,12 | %90,29 | %45,95 | %47,17 | 325 |
| 220003 | replay | %82,98 | %69,19 | %77,79 | %13,79 | %8,61 | 90 |

Her yöntem faz başına 40.000 örnekte 2.500, dört fazın toplamında 160.000
örnekte **10.000 güncelleme** yaptı; geçiş penceresinde (faz 4 ilk 1.000
örnek) üç tohumda da 62 güncelleme düştü.

### Okuma: unutma görünür, ama replay "iyidir" düz okuması yanlış

- **Unutma büyük ve tutarlı.** A'da faz 2→3 hasarı üç tohumda ~%46: öğrenci
  M2/R2'ye geçince M2/R1 kuralını neredeyse çökme düzeyinde kaybediyor
  (faz3 ~%42, dört sınıfta şans %25'e yakın değil ama tavandan çok uzak).
  Kendi faz 2 referansına göre ölçüldüğü için bu öğrenilemezlik tabanı
  değil, gerçek unutmadır. Etki penceresi görünür: aranılan olgu bu düzende
  mevcut. D₁₀₀₀ (A) ~310–328.

- **Replay hasarı üçte bire indiriyor** (~%14–16) ve D₁₀₀₀'i A'nın yaklaşık
  üçte birine (~90–150) düşürüyor. Yön üç tohumda da aynı.

- **Ama replay son göreve tam uyumu engelliyor.** Faz 4 (R1/M2) sonunda A
  M2/R1'de ~%90'a dönerken replay ~%78'de kalıyor; A'nın faz 4 donmuş
  doğruluğu replay'inkinden **~12 puan yüksek**. Replay geçmiş R1'i tamponda
  tuttuğu için faz 3'te (R2/M2) yeni kurala uyumu ciddi biçimde bozuluyor:
  replay'in faz 3 toplam kâhin pişmanlığı ~18.000–19.000, A'nınki ~7.000 —
  iki katından fazla. Replay **unutmayı kaldırmıyor, dengeyi kaydırıyor**:
  eski kuralı daha iyi koruyor, güncel kurala uyumu geciktiriyor.

- **Hasar/toparlanma ayrıştırması D₁₀₀₀ uyarısını doğruladı.** A hızlı
  unutup hızlı geri öğreniyor (yüksek hasar, yüksek toparlanma); replay az
  kaybettiği için toparlanacak az şeyi var (düşük hasar, düşük toparlanma).
  D₁₀₀₀ tek başına bu iki rejimi ayırmazdı; üç donmuş kopya ayırdı.

### Sınırlar ve sonraki adım

Üç tohum tek tek gösterildi; onaylayıcı havuzlama yok. Kapı geçilmediği için
bu bir hipotez testi değil, etki penceresi keşfidir. Öğrenci %90 tavana
oturuyor; bu tavanın altındaki her şey öğrenilebilirlik sınırıyla
karışabilir. Replay'in "eski kuralı koru / yeni kurala uyumu geciktir"
dengesi tek yönlü bir iyilik değildir; hangi ucun istendiği görev tanımına
bağlıdır.

Etki penceresi görünür olduğundan, önkayıt sırasına göre bundan sonrası:
Hat 2 (v0.4) kabul ve kapısı; kapı geçerse bu bulgular önkayıtlı protokolde
10+ eşleştirilmiş jeneratör–eğitim tohumuyla doğrulanır. Yönlendirme ve
yenileme koşulları da ancak o zaman, keşif değil doğrulama olarak eklenir.
Hat 1'in hiçbir sayısı Hat 2 ayarını belirlemedi.

---

## Hat 2 — v0.4 onaylayıcı deney spesifikasyonu (yalnızca belge)

Bu bölüm sonuçlardan önce sabitlendi. **Bu turda çalıştırılmadı;** yalnızca
gelecekteki onaylayıcı deneyin kararlarını kaydeder. Hat 1'in hiçbir sayısı
bu ayarları belirlemez. Marj tanısı Hat 1 keşfinden önce yapıldığı için,
Hat 1'den bir hipotez seçilirse bu deney "keşiften türetilmiş, yeni veride
önkayıtlı doğrulama"dır; "keşiften tamamen bağımsız" denmez.

### Ortak marj filtresi

- **τ = 0,25 normalize marj.** Bir örnek yalnızca **her iki kural altında da**
  normalize marjı ≥ τ ise akışa girer. Tek kuralla filtre faz 3–4 girdi
  dağılımını bozardı; ortak filtre aynı karışım içinde girdi dağılımını kural
  değişiminden bağımsız tutar. M1→M2 kayması korunur (faz 1→2 kontrolünün amacı).
- **Normalizasyon ölçekleri filtresiz kalibrasyonda hesaplanıp dondurulur.**
  Her jeneratör-kural için bağımsız eşit M1/M2 karışımında; marj tanısındaki
  tanımla aynı (tüm skor elemanları üzerinden popülasyon std).
- **Dışlama tavanı %30, M1 ve M2 için ayrı.** Herhangi bir karışımda atılan
  örnek oranı %30'u aşarsa tasarım başarısızdır; v0.4 reddedilir.

### Ofset: yeniden ayarlanmaz

Ofset öğretmenin özelliğidir; filtre girdi üzerinde bir seçimdir. Ofset
filtre sonrası **yeniden ayarlanmaz**; aksi hâlde v0.3 ile karşılaştırılabilirlik
kaybolur ve "filtre etkisi" ile "ofset etkisi" karışır. Filtrelenmiş
dağılımda denge bandı bozuluyorsa bu bir **kabul redidir**, düzeltme sebebi
değildir; o durumda v0.4 başarısız sayılır ve kapı tanımı (0,9 notu kayıtta)
sürüm artışıyla yeniden ele alınır.

### Kabul ve kapı

Denge ve uyuşmazlık ölçütleri **filtrelenmiş dağılımda yeniden sınanır**;
bantlar v0.3'ten değişmez. Kabul başarısızsa kapıya geçilmez. Kabul edilirse
kapı, mevcut sabit öğrenci protokolü ve değişmemiş 0,9 formülüyle denenir.
Kapı geçilirse Hat 1 bulguları önkayıtlı protokolde 10+ eşleştirilmiş
jeneratör–eğitim tohumuyla yeniden koşulur. Kapı geçilmezse öğrenci
değil kapı tanımı sorgulanır; çevrimdışı referans temelli yeni kapı ancak
açık gerekçe, sürüm artışı ve yeni önkayıtla tanımlanır.

---

## Hat 1 — Etki penceresi keşif koşusu (önkayıt)

**Öğrenilebilirlik kapısı geçilmedi; bu koşu hipotez testi değil, etki
penceresi keşfidir.** Bu bölüm sonuçlardan önce sabitlendi. Hat 1'in hiçbir
sayısı Hat 2 (v0.4) ayarını belirlemez. Bulgu keşiftir; yönlendirme ve
yenileme ancak unutma görünürse, yine keşif etiketiyle eklenir.

### Sabit yapılandırma

| Ayar | Değer |
|---|---|
| Jeneratör | v0.3, öğretmen tohumu 1000, paylaşım 0,5, gürültü %5 |
| Öğrenci | 32 girdi → 64 gizli → 4 çıktı, bağlam yok |
| Optimizasyon | Adam, sabit lr 0,001; söndürme yok |
| Minibatch | 16, grup sonunda güncelleme; son eksik grup atılmaz |
| Fazlar | R1/M1 → R1/M2 → R2/M2 → R1/M2 |
| Faz uzunluğu | 40.000 örnek (kapı eğitim bütçesiyle aynı) |
| Yöntemler | A (replaysiz) ve replay (reservoir 512, batch 8) |
| Eğitim/akış tohumları | 220001, 220002, 220003 (üç eşleştirilmiş koşu) |
| Bağımsız M2/R1 değerlendirme | geçmiş 221000, akış 221001, 20.000 örnek |
| Geçiş penceresi | Faz 4 ilk 1.000 örnek |

A ve replay her tohumda **aynı başlangıç ağırlıklarının deepcopy kopyasını
ve aynı gürültülü akışı** kullanır (pilot düzenindeki gibi). Başlangıç modeli
tohumu 7. Jeneratör tüm koşularda 1000 sabittir; jeneratör değişkenliği
Hat 2'nin işidir ve buraya karıştırılmaz.

### Birincil ölçüm: D₁₀₀₀ (kendi referansına göre)

Her yöntem-tohum için faz 2, faz 3 ve faz 4 sonunda modelin donmuş kopyası
saklanır. D₁₀₀₀, faz 4'ün ilk 1.000 örneğinde, öğrenmeye devam eden model
ile **kendi faz 2 sonu donmuş kopyasının** aynı örneklerdeki temiz hata
farkının toplamıdır:

    D_1000 = sum_{t=1..1000} [ 1(faz4_tahmin_t != temiz_t)
                             - 1(faz2donmuş_tahmin_t != temiz_t) ]

Pozitif D₁₀₀₀, faz 2 performansına göre geçiş penceresindeki toplam ek
hatadır (unutma ile yeniden öğrenmeyi birlikte içerir). Kâhin pişmanlığı
tanımı değişmez; faz başına kâhin pişmanlığı ikincil ölçüm olarak korunur.

### Ayrıştırma: üç donmuş kopya, tek bağımsız değerlendirme

Faz 2, faz 3 ve faz 4 sonu donmuş kopyaları **aynı** bağımsız M2/R1
akışında (20.000 örnek) değerlendirilir. Tek tabloda, yöntem ve tohum
başına ayrı satır:

- **hasar = faz2_M2R1_doğruluk − faz3_M2R1_doğruluk** (pozitif = kayıp;
  unutma, yeniden öğrenme karışmadan).
- **toparlanma = faz4_M2R1_doğruluk − faz3_M2R1_doğruluk** (pozitif = iyileşme).
- D₁₀₀₀ = geçiş penceresindeki toplam bedel.

Faz 4 dağılımı M2/R1 olduğundan referans her yöntemin **kendi** faz 2 sonu
modelidir; %87 bir tavan değil, belirli bütçedeki ölçümdür. Üç tohum tek
tek gösterilir; üçünden onaylayıcı sonuç çıkarılmaz.

### Kayıt ve etiket

Her koşu faz 2/3/4 ağırlıklarını, dört fazlı akışın örnek sırasını, temiz
ve gürültülü hedefleri, tahminleri, geçiş penceresi güncelleme sayısını ve
bütünlük özetlerini kalıcı saklar; kayıtlar yüklenip doğrulanır. Tüm çıktı
**keşif** etiketini taşır. Sonuç dizini Hat 2'den ayrıdır.

### Beklenen okuma

- Unutma görünürse (D₁₀₀₀ pozitif ve/veya hasar belirginse): yönlendirme
  ve yenileme koşulları keşif etiketiyle eklenebilir.
- Görünmüyorsa: faz uzunluğu ve uyuşmazlık ayarı gündeme gelir.
Her iki okuma da keşiftir; Hat 2 onaylayıcı deneyi bunu bağlamaz.

---

## Marj tanısı sonucu: öngörüyle kısmen tutarlı, dal kesin değil

Uygulama: [`margin_v03.py`](margin_v03.py);
testler: [`test_margin_v03.py`](test_margin_v03.py);
tam sonuç: [`results_margin_v03/summary.json`](results_margin_v03/summary.json);
kalıcı model ve tahmin kayıtları: [`results_margin_v03/records/`](results_margin_v03/records).

**63 yazılım testi geçti.** Bu tur yalnızca eski birleşik öğrenciyi ve
v0.3 ana öğrencisini değişmeyen ayarlarla yeniden üretti, kayıtları
doğruladı ve marj tanısını çalıştırdı. Öğrenci, jeneratör, kabul ölçütü
ve kapı formülü değişmedi; **v0.4 başlatılmadı.**

### Yeniden üretim doğrulaması

- v0.3 ana öğrenci: başlangıç özeti, güncelleme sayısı (2.500), temiz
  doğruluk (%87,435), karışıklık matrisi, **final ağırlık SHA-256** ve
  değerlendirme hedef özetleri kayıtla birebir eşleşti. Tahmin dizisi
  eşitliği kanıtlandı.
- Eski birleşik öğrenci: başlangıç özeti, güncelleme sayısı (2.500),
  temiz doğruluk (%93,59) ve karışıklık matrisi eşleşti. Final ağırlık ve
  tahmin dizisi kayıtlı olmadığından **tahmin dizisi eşitliği kanıtlanmadı**.
- Her iki modelde skorların argmax'ı, kayıt için kullanılan temiz
  hedeflerle eşleşti; bu olmasaydı tanı tasarım gereği dururdu.

### Marj dağılımı ve hata yoğunlaşması

Normalize marj = ham marj / σ_s; σ_s her jeneratör-kural için bağımsız
eşit M1/M2 karışımında (20.000) hesaplandı. Değerlendirme her model için
kendi M1/R1 akışında, 20.000 örnek.

| Ölçüt | Eski birleşik | v0.3 ana |
|---|---:|---:|
| Toplam temiz hata | 1.282 | 2.513 |
| Normalize marj < 0,1 payı | %5,48 | %12,17 |
| En düşük beşlik hata payı | %90,25 | %62,55 |
| Yoğunlaşma bayrağı (≥%70) | Sağlandı | **Sağlanmadı** |

### Yorum: sınır kütlesi arttı ama dal tek başına belirlenemiyor

- **Sınıra yakın kütle arttı.** Normalize marjı 0,1 altında kalan örnek
  payı %5,48'den %12,17'ye, iki katından fazla yükseldi. Bu, dengeleme
  ofsetinin karar sınırlarını yoğun bölgelere kaydırdığı mekanizmasıyla
  tutarlıdır. Ancak öğretmen tohumu ve kalibrasyon da değiştiği için bu
  fark yalnızca ofsetin yalıtılmış nedensel etkisi değildir; skor marjı
  geometrik sınıra uzaklığın doğrudan ölçüsü de değildir.
- **Hata yoğunlaşması jeneratör kolunu tek başına doğrulamıyor.** Eski
  modelde hatalar en düşük marj beşliğinde yoğunlaşırken (%90,25), v0.3'te
  yoğunlaşma %62,55 ile önkayıtlı %70 eşiğinin altında. v0.3'te hatalar
  marj boyunca eski modele göre daha yayık. Önkayıtlı ölçüte göre v0.3 için
  **sınırda yoğunlaşma ölçütü sağlanmadı**; jeneratör (öğretmen keskinliği)
  koluna kesin geçiş için yeterli yoğunlaşma yoktur.
- **3. dal (öğrenci/optimizasyon) açık kalıyor.** Kapı koşusunda eğri geç
  dönemde hâlâ yükseliyordu ve kapasite monoton yardım etmişti; artan
  sınır kütlesi bu açıklamayı dışlamaz. Bu tanı hipotez testi değildir ve
  nedenleri birbirinden kesin ayırmaz.

### Sonuç ve durma

İki bulgu birlikte "sınır kütlesi arttı, ama v0.3 hataları tek bir düşük
marj beşliğinde toplanmıyor" diyor. Bu, ne saf jeneratör kolunu ne de saf
öğrenci kolunu doğrulayan karışık bir sonuçtur. Önkayıtlı ölçüt tek başına
v0.4 yolunu seçmeye yetmez.

Bu nedenle v0.4 bu turda **başlatılmadı** ve hiçbir müdahale (ortak marj
filtresi τ, daha basit öğretmen, kapı formülü) uygulanmadı. Bir sonraki
tur için müdahale, τ veya öğretmen değişikliği ve durma kuralı, yine
sonuçlar görülmeden ayrı bir önkayıtta sabitlenmelidir. Bu turda üretilen
iki model ve tahminleri, sonraki analizler yeni eğitim gerektirmesin diye
kalıcı olarak kaydedildi.

---

## Marj tanısı önkayıtı — yeniden üretim ve kayıt politikası

Bu bölüm marj sonuçları görülmeden kaydedildi. Bu tur yalnızca eski
birleşik öğrenci ve v0.3 ana öğrencisinin deterministik yeniden üretimi,
kayıt doğrulaması ve marj tanısını kapsar. Öğrenci, jeneratör, kabul
ölçütleri ve kapı formülü değişmez. **v0.4 başlatılmaz.**

### Yeniden üretim ve zorunlu eşleşme

- Eski birleşik koşu: pilot jeneratörü, öğretmen tohumu 7; başlangıç
  modeli tohumu 7; 32→64→4, minibatch 16, sabit öğrenme oranı 0,001.
  Eğitim, 107 tohumlu 10.000 örnek ile 108 tohumlu 30.000 örneğin
  sıralı birleşimidir. Değerlendirme geçmişi 707, asıl akışı 708;
  değerlendirme M1/R1 altında 20.000 örnektir.
- v0.3 ana öğrenci: öğretmen tohumu 1000, başlangıç modeli tohumu 7;
  aynı öğrenci ayarları; 120100 tohumlu 40.000 eğitim örneği.
  Değerlendirme geçmişi 120300, asıl akışı 120301; M1/R1, 20.000 örnek.
- Her iki yeniden üretimde başlangıç özeti, güncelleme sayısı,
  temiz/gürültülü doğruluk ve karışıklık matrisi eski kayıtla eşleşmelidir.
  v0.3 için ayrıca final ağırlık SHA-256 özeti ile değerlendirme hedef
  özetleri birebir eşleşmelidir.
- Herhangi bir zorunlu eşleşme başarısızsa **hata–marj tanısı durur**;
  tolerans gevşetilmez, önce fark araştırılır.
- Eski birleşik koşunun final ağırlıkları ve tahmin dizisi kaydedilmemişti.
  Başarılı özet eşleşmesinde dahi **“tahmin dizisi eşitliği kanıtlanmadı”**
  notu korunur. Bu yeniden eğitimdir, ancak yeni ayar araması değildir.

### Marj ölçümü ve bağımsız ölçek kalibrasyonu

Temiz skorlar, ortak ve özgü bileşenlerin toplamıdır; v0.3'te kuralın
sınıf ofsetleri de dahildir. Ham marj, en yüksek iki skorun farkıdır.
Normalize marj = ham marj / σ_s.

σ_s her jeneratör ve kural için ayrı, eşit M1/M2 karışımından toplam
20.000 örnekte hesaplanır: M1'den 10.000 ve M2'den 10.000.
Birleşik skor matrisinin tüm örnek ve sınıf elemanları üzerinden
popülasyon standart sapması kullanılır; bölen eleman sayısıdır.
Ek örnek-başına veya sınıf-başına merkezleme uygulanmaz.
Eski jeneratörün ölçek kalibrasyonu tohumu **130000**, v0.3'ünki
**130100**; bu akışlar eğitim, değerlendirme, kabul ve ofset
kalibrasyonundan ayrıdır. Sıfır veya sonlu olmayan ölçek tanıyı durdurur.

Normalize marjın **0,1 / 0,25 / 0,5 değerlerinin kesin olarak altında**
kaldığı örnek payları üç eşik için de raporlanır; sonuca göre eşik
seçilmez. Ham ve normalize marj nicelikleri birlikte gösterilir.

Öğretmenlerin dağılım karşılaştırması için ayrıca M1'de **130200**,
M2'de **130201** tohumlu, karışım başına 20.000 örnek kullanılır.
İki jeneratör aynı gizli örnekleri paylaşır; her örnekte R1 ve R2
skorları değerlendirilir. Bu öğretmen tanısıdır, M2 öğrenci kapısı
değildir; modeller bu ek akışlarda eğitilmez.

Hata–marj eşleştirmesi ise her modelin kendi özgün M1/R1 değerlendirme
akışında yapılır. Tam hassasiyetli gizli örnekler yeniden üretilir;
yuvarlanmış gözlemlerden ters izdüşümle yaklaşık gizli örnek türetilmez.
Skorların seçtiği sınıf, kayıt için kullanılan temiz hedefle eşleşmelidir.

### Beşlikler ve tanı kararı

Her modelin değerlendirme örnekleri artan marja göre sıralanır;
eşit marjlarda özgün örnek sırası korunur. Sıralı örnekler beş eşit
büyüklükte gruba ayrılır. Her grupta örnek sayısı, marj aralığı, hata
sayısı, grup içi temiz hata oranı ve toplam temiz hatalardaki pay verilir.
Toplam hata sıfırsa hata payı ve yoğunlaşma kararı tanımsız raporlanır.

v0.3 ana öğrencisinin toplam hatalarının en az %70'i en düşük marj
beşliğindeyse sonuç **sınırda yoğunlaşma ölçütü sağlandı** olarak
raporlanır. Sağlanmazsa bu ölçüte göre jeneratör koluna geçiş için
yeterli yoğunlaşma yoktur; öğrenci/optimizasyon açıklamaları açık kalır.
Bu eşik hipotez testi veya nedenlerin birbirini dışladığı bir kanıt
değildir. “Kapasite ve süre makul bütçede kapıyı geçiremez” iddiası
kanıtlanmamış bir tahmindir; bu tanıdan çıkarılmayacaktır.

Kendi beşlikleri her dağılımda yaklaşık %20 örnek içerdiğinden eski–yeni
düşük marj kütlesi karşılaştırması beşlik büyüklükleriyle yapılmaz.
Ortak mutlak normalize eşikler ve marj nicelikleri kullanılır.
Öğretmen tohumu ve kalibrasyon mekaniği de değiştiği için eski–yeni fark
yalnızca ofsetin nedensel etkisi değildir. Skor marjı, geometrik sınıra
uzaklığın doğrudan ölçüsü de değildir.

### Bugünden itibaren zorunlu eğitim kayıtları

Her yeni eğitim koşusu final ağırlıklarını ve örnek başına tahminleri
kalıcı olarak kaydeder. Kayıtlar eğitim/değerlendirme ayrımını, örnek
sırasını, temiz ve gürültülü hedefleri, model mimarisini, tohumları,
ayarları ve kaynak/sürüm bilgisini içerir. Son ağırlık ve veri dosyaları
için bütünlük özetleri saklanır; kayıt yükleme doğrulaması yapılır.
Yalnızca doğruluk veya karışıklık matrisi saklamak yeterli değildir.

Bu turda iki yeniden üretilen modelin final ağırlıkları, çevrimiçi
eğitim tahminleri ve değerlendirme örnekleri/tahminleri ayrı dosyalarda
saklanacak; marj dizileri örnek sırasıyla eşleştirilecektir. Eski sonuç
dosyalarının üzerine yazılmayacak. Eski deney giriş noktaları bu kayıt
politikasına uyarlanmadan yeni araştırma koşuları için kullanılmamalıdır.

### Mevcut kapıyı değiştirmeyen protokol endişesi

Kapıdaki 0,9 katsayısı bir tasarım seçimidir; mevcut kayıtta öğretmen
karmaşıklığından türetilmiş bir gerekçesi yoktur. Formül sınıf paylarını
görür, öğretmen karmaşıklığını veya marj dağılımını görmez. Denge
sağlanınca dar bir mutlak doğruluk bandı istemesi, öğrenilebilirliğin
tek olası tanımı değildir. **Bu tur katsayı veya formül değiştirilmez.**

Gelecekte v0.4 de kapıyı geçmezse kapı tanımının uygunluğu ayrıca
sorgulanabilir; bu otomatik olarak kapının yanlış olduğu anlamına gelmez.
Öğretmen karmaşıklığını hesaba katan çevrimdışı referans temelli bir kapı
ancak açık gerekçe, sürüm artışı ve yeni önkayıtla tanımlanabilir.
Referansın eğitim bütçesi, mimarisi, bağımsız değerlendirmesi ve oran
katsayısı sonuçlardan önce sabitlenir; sessiz veya geriye dönük
eşik düzeltmesi yapılmaz.

Gelecekte ortak marj filtresi seçilirse her iki kuralın koşulu birlikte
aranmalıdır: bu, **aynı karışım içinde** girdi dağılımını kural
değişiminden bağımsız tutar; M1→M2 kayması korunur. Denge, uyuşmazlık
ve atılan örnek oranı filtrelenmiş dağılımda yeniden ölçülmelidir.
Bu not bir v0.4 filtre eşiği seçimi veya uygulama izni değildir.

---

## Güncel sonuç: v0.3 temel öğrenci kapısı BAŞARISIZ

Uygulama: [`gate_v03.py`](gate_v03.py);
testler: [`test_gate_v03.py`](test_gate_v03.py);
tam sonuç: [`results_gate_v03/summary.json`](results_gate_v03/summary.json).

**56 yazılım testi geçti.** Aşağıdaki değerler gerçek kapı koşusuna
aittir; testlerde kullanılan yapay başarı senaryoları deney sonucu değildir.
Jeneratör kabulü ile öğrenci kapısı ayrı kontrollerdir: jeneratör 1000
kabul edilmiş olarak kalır, fakat sabit temel öğrenci kapıyı geçemedi.

### Ölçülen eşik ve sonuçlar

Bağımsız 20.000 örneklik M1/R1 kalibrasyonunda sınıf payları
%25,87, %24,00, %27,57 ve %22,56 bulundu. Çoğunluk payı %27,57:
ölçülen eşik = 0,2757 + 0,9 × (1 − 0,2757) = **%92,757**.
Bu eşik nominal %92,5–%93,5 bandının içindedir.

Üç model aynı 40.000 eğitim örneğiyle, minibatch 16 ve sabit öğrenme
oranı 0,001 ile eğitildi; her biri 2.500 güncelleme yaptı.
Ayrı 20.000 örneklik M1/R1 değerlendirmesinde ağırlıklar değişmedi.
Temiz ve gürültülü değerlendirme etiketlerinin özetleri üç modelde eşit;
başlangıç tohumu ortak olsa da farklı genişliklerin ağırlıkları aynı değildir.

| Gizli birim | Rol | Parametre | Temiz doğruluk | Wilson %95 | Karşılaştırma |
|---|---|---:|---:|---|---|
| 64 | Ana aday | 2.372 | %87,435 | [%86,968, %87,887] | Başarısız |
| 128 | Kapasite tanısı | 4.740 | %88,580 | [%88,132, %89,013] | Başarısız |
| 256 | Kapasite tanısı | 9.476 | %89,315 | [%88,879, %89,736] | Başarısız |

Ana adayın Wilson üst sınırı eşikten yaklaşık 4,87 yüzde puanı aşağıda;
önceden sabitlenen kurala göre karar **başarısız**, belirsiz değil.
Ana adayın nokta tahmini ile eşik arasındaki fark 5,322 yüzde puanıdır.
Wilson aralığı eğitilmiş modele ve ölçülen eşiğe koşulludur; eğitim
tohumu değişkenliğini ve eşik tahmini belirsizliğini kapsamaz.

### Sınıf bazlı tanı ve yorum sınırları

Ana aday için sınıf kimlikleri 0–3 sırasıyla:

| Sınıf | Destek | Geri çağırım | Hata sayısı |
|---|---:|---:|---:|
| 0 | 5.107 | %90,112 | 505 |
| 1 | 4.859 | %90,245 | 474 |
| 2 | 5.650 | %86,460 | 765 |
| 3 | 4.384 | %82,459 | 769 |

Toplam 2.513 temiz etiket hatası vardır. En büyük çift yönlü karışma
2↔3 arasındadır (436 + 370 = 806 hata); ancak hatalar bu çiftle sınırlı
değildir. Hiçbir sınıfın geri çağırımı %80'in altında değildir.
Dolayısıyla eski nadir-sınıf çöküşü açıklaması bu koşuda gözlenmiyor.
Karışıklık matrisi tek başına hataların karar sınırına uzaklığını ölçmez;
kesin bir öğretmen keskinliği teşhisi çıkarılmaz.

Ana adayın çevrimiçi temiz doğruluğu 10.000'inci örnekte biten blokta
%81,1, 30.000'de biten blokta %86,9 ve son blokta %87,3'tür.
Son on blok %85,0–%88,2 aralığındadır. Bu, erken döneme göre ilerleme
olduğunu gösterir; kesin plato veya yakınsama kanıtı değildir.
Daha uzun eğitimin kapıyı geçireceği de bu veriden çıkarılamaz.

Genişlik artışı bu tek koşuda doğruluğu artırdı, fakat 256 birim de
eşiğin altında kaldı. Bu sonuç ne kapasitenin etkisizliğini ne de tek
darboğaz olduğunu kanıtlar. Süre/adım, optimizasyon ve temsil etkileri
ayrıştırılmadı. Eski jeneratörle elde edilen doğrulukla fark, ofsetin
nedensel etkisi olarak sunulmaz.

### Durma kararı

Önceden yazılan protokol gereği bu kapı turu burada durdu:
- Ana aday veya jeneratör değiştirilmedi; 128/256 tanıları ana adayın
  yerine geçirilmedi.
- Eşik, öğrenme oranı, minibatch ve eğitim süresi gevşetilmedi.
- M2 değerlendirmesi yapılmadı; ana adayın geçmesi koşulu sağlanmadı.
- A+bağlam, yönlendirici, yenileme, faz uzunluğu pilotu ve dört faz
  çalıştırılmadı.

(c) bağlam kararı aşağıdaki protokolde kayıtlıdır; temel kapı başarısızlığı
bu modüllerin denenmiş olduğu anlamına gelmez. Yeni bir tanı turu için
müdahale ve durma kuralları yeniden sonuç görülmeden kaydedilmelidir.
Mevcut sonuçlar tek jeneratör–eğitim tohumu çiftine ait keşifsel bulgulardır;
ana deneyin en az 10 eşleştirilmiş çift gereksiniminin yerine geçmez.

---

## v0.3 sağlamlık kontrolü ve kapı öncesi sabit protokol

Bu protokol, 20 adaylık sağlamlık kontrolünden sonra ve **v0.3 öğrenci
eğitimi/kapı sonuçları görülmeden** kaydedildi. Aşağıdaki ayarlar bu kapı
turunda sonuçlara göre değiştirilmeyecek.

### Sağlamlık kontrolü: 14/20 kabul (%70)

Uygulama: [`robustness_v03.py`](robustness_v03.py);
testler: [`test_robustness_v03.py`](test_robustness_v03.py);
aday başına tüm ölçümler:
[`results_robustness_v03/summary.json`](results_robustness_v03/summary.json).

1000–1019 öğretmen tohumlarının tamamı, erken durmadan, metrik tohumları
50000–50019 ile değerlendirildi. Her karışım için 20.000 örnek kullanıldı.
Ofset her adayda yeniden hesaplandı; kabul ölçütleri değiştirilmedi.

| Sonuç | Aday sayısı |
|---|---:|
| Kabul | 14 |
| Yalnızca denge nedeniyle red | 6 |
| Yalnızca uyuşmazlık nedeniyle red | 0 |
| Her iki nedenle red | 0 |

**Seçilmiş jeneratör 1000 olarak kalır.** Bu bir seçim veya eğitim
deneyi değildir. İncelenen aralıkta kabul yalnızca tek bir tohuma özgü
değildir; ancak %70, popülasyon kabul olasılığının garantisi değildir.
200 denemelik tavanın yeterliliği veya ana deneyin istatistiksel gücü
buradan çıkarılmaz. 14 kabul edilmiş aday, en az 10 eşleştirilmiş
jeneratör–eğitim tohumu koşusunun yapılmış olduğu anlamına gelmez.
Bu aşamada **50 yazılım testi geçti**.

### Bağlam kararı: (c)

- A/C temel öğrencileri yalnızca 32 güncel gözlem boyutunu alır.
- B/D uzmanları da aynı 32-girdili temel mimariyi kullanır.
- B/D yönlendiricisi, son 64 gözlenmiş gürültülü etiketli örneğin
  132-boyutlu özetini alır. Güncel veya gelecek etiket, temiz etiket ve
  gerçek rejim kimliği çevrimiçi öğrenciye verilmez.
- Ayrı **A+bağlam** tanısı, 32 gözlem ve aynı 132 özeti birleştiren
  164-girdili, yönlendirmesiz bir ağdır.
- Bağlam penceresi faz geçişinde sıfırlanmaz; yalnızca tahminden sonra
  güncel gözlem ve gürültülü etiketle güncellenir.

A+bağlam ile A karşılaştırması bağlam eklemenin toplam etkisini ölçer;
girdi genişliği ve parametre sayısı da değişir. B ile A+bağlam
karşılaştırması aynı bağlam bilgisine erişen farklı mimarileri karşılaştırır.
Kapasite, hesaplama ve eğitim bütçesi denetlenmeden bu fark "saf yapısal
katkı" diye yorumlanmaz. Prob sonuçları 132 boyutun zorunluluğunu kanıtlamaz;
bu seçim temel öğrenilebilirliği yönlendirme mekanizmasından ayırmak içindir.

### Sabit öğrenci ve tek turluk kapasite kontrolleri

| Ayar | Sabit değer |
|---|---|
| Jeneratör | v0.3, öğretmen tohumu 1000, paylaşım 0,5, gürültü %5 |
| Ana aday | 32 girdi → 64 gizli birim → 4 çıktı |
| Aktivasyon | ReLU |
| Optimizasyon | Adam, sabit öğrenme oranı 0,001; söndürme yok |
| Kayıp | Gürültülü etiketlerde çapraz entropi |
| Eğitim | M1/R1, 40.000 örnek, tek geçiş |
| Minibatch | 16, her grubun sonunda güncelleme |
| Başlangıç modeli tohumu | 7 |
| Eğitim akışı tohumu | 120100 |
| Eşik kalibrasyonu tohumu | 120200 |
| M1 değerlendirme geçmişi / akışı | 120300 / 120301 |
| Koşullu M2 değerlendirme geçmişi / akışı | 120400 / 120401 |
| Eşik kalibrasyonu ve değerlendirme büyüklüğü | Ayrı ayrı 20.000 |
| Çevrimiçi öğrenme eğrisi blokları | 1.000 örnek |

Bu akışlar ofset, jeneratör kabulü, sağlamlık kontrolü ve prob akışlarından
ayrıdır. 40.000 örnek 2.500 güncelleme verir. Faz geçişindeki 1.000
örneklik pencereye grup hizasına göre 62 veya 63 güncelleme düşer;
faz pilotunda gerçek sayı raporlanır. Tahmin her zaman etiketten önce
yapılır; son eksik grup atılmaz.

128 ve 256 gizli birim, aynı eğitim/değerlendirme verilerinde ve aynı
başlangıç tohumu ile **yalnızca kapasite tanıları** olarak çalıştırılır.
Farklı genişlikler aynı başlangıç ağırlıkları demek değildir. Ana aday
64 birimdir; en iyi değerlendirme sonucunu seçme yapılmaz. Büyük bir
modelin kapıyı geçmesi, 64 birimli ana adayın kararını değiştirmez.
A+bağlam ve yönlendirici bu temel kapı turunda eğitilmeyecek.

### Kapı kararı ve koşullu M2 raporu

Eşik, bağımsız M1/R1 kalibrasyon akışında ölçülen temiz çoğunluk payı
üzerinden hesaplanır: taban + 0,9 × (1 − taban). Nominal bant
%92,5–%93,5 olarak kalır; kabul raporundaki paylardan eşik alınmaz.

Ana adayın ayrı 20.000 örnekte dondurulmuş temiz doğruluğu ve Wilson
%95 aralığı raporlanır. Alt sınır ölçülen eşiğin üstündeyse **geçti**,
üst sınır eşiğin altındaysa **başarısız**, diğer durumlarda **belirsiz**.
Bu aralık tek eğitilmiş modele koşulludur; eğitim tohumu değişkenliğini
ve eşik tahmininin belirsizliğini kapsamaz.

Her genişlik için temiz/gürültülü doğruluk, sınıf destekleri, geri çağırım,
karışıklık matrisi, öğrenme eğrisi, parametre ve güncelleme sayısı kaydedilir.
Ana aday geçerse aynı donmuş model M2/R1'de değerlendirilir; yeniden
eğitim veya ayar seçimi yapılmaz. Başarısız/belirsiz sonuçta bu tur durur;
128/256 kontrolü ana adayın yerine geçirilmez.

### Ek modül kontrolleri ve dört faza geçiş sınırı

Temel kapının geçilmesi B/D sisteminin öğrenilebilirlik onayı değildir.
Yönlendirme uygulanmadan önce ayrı protokolde şu kontroller sabitlenecek:

1. Her uzman, kapıdaki aynı mimari ve optimizasyonla kendi kuralında
   tek-rejim öğrenilebilirlik kontrolünden geçer; R2 başarısı R1'den
   varsayılmaz. Gerçek kural kimlikleri yalnızca tanı düzeninde kullanılabilir.
2. Aynı uzmanlarla ideal yönlendirme tanısı ile öğrenilmiş yönlendirme
   karşılaştırılır. Uzman hatası, yönlendirme hatası ve uçtan uca hata
   ayrı raporlanır. Gerçek rejim kimliği öğrenilmiş yönlendiriciye verilmez.
3. Yönlendiricinin hedefi, güncellemesi, mimarisi, veri akışları ve başarı
   eşiği kendi sonuçları görülmeden kaydedilir. Mevcut özet probu bu
   uçtan uca kontrolün yerine geçmez.
4. A+bağlam tanısının mimarisi ve kaynak maliyeti ayrıca raporlanır;
   temel kapı başarısı bu farklı girdili ağın başarısı olarak sunulmaz.

Temel kapı ve M2 raporundan sonra faz uzunluğu pilotu için sayısal etki
penceresi ve durma kuralı ayrıca önceden sabitlenecek. Kural uyuşmazlığı
değiştiği için A'nın "görünür ama toptan değil" başarısızlığı eski
pilottan devralınmaz. Bu kapı turu dört fazı, yönlendirmeyi veya yenilemeyi
başlatmaz; ana deney en az 10 eşleştirilmiş jeneratör–eğitim tohumu
gereksinimini korur.

---

## v0.3 jeneratör kabulü: BAŞARILI (en güncel durum)

Uygulama: [`generator_v03.py`](generator_v03.py), testleri
[`test_generator_v03.py`](test_generator_v03.py), sonuçları
[`results_generator_v03/summary.json`](results_generator_v03/summary.json).
Mevcut pilot, tanı ve v0.2 dosyaları değişmedi; dört fazlı deney
çalıştırılmadı. **47 test geçti.**

Çalıştırma:

    python continual_pilot/generator_v03.py

### Neden v0.3 (spesifikasyon düzeltmesi, jeneratör düzeltmesi değil)

v0.2 dengeyi red-örneklemesine bırakmıştı. Kısıt 16 eşzamanlı dar-bant
koşulu (4 sınıf × R1/R2 × M1/M2); rastgele öğretmenlerin karar bölgeleri
dengeli sınıf paylarını kendiliğinden sağlamaz. Denenen 200 adayda kabul
bulunmaması **imkânsızlık veya sıfır kabul olasılığı kanıtı değildir**.
Bu koşullar birbirinden bağımsız da değildir; tekil olasılıkları çarparak
ortak kabul olasılığı hesaplanamaz. Tasarım sorunu, **dengeyi inşa etmek
yerine şansa bırakan spesifikasyondur**. v0.3 karışık marjinalde dengeyi
kalibrasyonla hedefler; red-örneklemesini bağımsız doğrulama olarak tutar.

### Yöntem: sınıf başına additif ofset

Skorlara kural başına sabit ofset eklenir:

    s_r(z) = α·h_ortak(z₁,z₂) + h_özgü(z_r) + β_r,  β_r ∈ ℝ⁴

β_r, M1∪M2 eşit karışımından bağımsız tohumlu örneklemde iteratif
log-oran düzeltmesiyle bulunur: **β ← β + η·log(hedef/gözlenen)**, sabit
50 iterasyon, sabit η = 0,5, hedef her sınıf ¼. Ofset additif sabit
olduğundan ortak/özgü altfonksiyonlar ve sınıf sayısı korunur.
Karar sınırları ve marjlar değişebileceği için öğrenci açısından görev
zorluğunun değişmediği varsayılmaz; öğrenilebilirlik kapıda ölçülür.
Ofset öğretmene bağlı olduğundan **her aday tohumda yeniden hesaplanır**.

**Önemli sınır:** Ofset her kuralın **kalibrasyon karışımındaki marjinalini**
¼'e yaklaştırmayı hedefler; sonlu örneklem ve sabit iterasyon sayısı
popülasyon düzeyinde tam eşitliği garanti etmez. Kabul R1/R2 × M1/M2
kırılımını ayrı ölçer. Kırılımdaki sapma bandı aşarsa tohum yine reddedilir.
%18–35 bandındaki tolerans, bu sapmalara alan bırakır.

### Kabul sonucu: seed 1000, ilk denemede, 0 red

| Metrik | Değer |
|---|---|
| Kabul edilen tohum | 1000 (ilk deneme) |
| Reddedilen | 0 |
| En küçük sınıf payı (16 koşul) | %22,34 |
| En büyük sınıf payı (16 koşul) | %28,98 |
| M1 uyuşmazlığı | %59,17 |
| M2 uyuşmazlığı | %58,51 |

Dört sınıf payı, dört koşulun (M1/M2 × R1/R2) tümünde **%22,3–%29,0**
aralığında; kabul bandı %18–35. Uyuşmazlık M1'de %59,165 ve M2'de
%58,505: %40–70 bandının içinde, orta noktası %55'in üzerindedir.
v0.2'nin 200 adaylık aralığı ile v0.3'ün tek kabul edilmiş adayını
karşılaştırmak, ofsetin nedensel etkisini ölçen eşleştirilmiş deney değildir.
Uyuşmazlığın değişim yönüne ilişkin önceden öngörü verilmemişti.

Daha düşük uyuşmazlık, kural geçişinde daha az örneğin temiz etiketinin
değişmesi demektir; bu, faz 3–4 etkisini küçültebilir. Öğrencinin hata
artışı bundan doğrudan hesaplanamaz. A koşulunun "görünür ama toptan değil"
başarısızlık penceresi faz pilotunda yeniden ölçülecek; eski pilottan
devralınmayacak.

Bağımsız karışım doğrulamasında her iki kuralın payları %25 hedefinin
±2 yüzde puanı içindedir (R1: %24,24–%26,12). Bu akış ofseti hesaplayan
kalibrasyon örneklemi değildir; bu ölçüm kabul koşullarına eklenmemiştir.

### Prob teşhisi: öngörüyle tutarlı, keşifsel bulgu

| Prob | Eski pilot jeneratörüyle v0.2 tanısı | v0.3 jeneratörü |
|---|---:|---:|
| Tam 132-boyut özet | %95,9 | %100 |
| Yalnızca 4-sıklık | %100 | %65,4 |

Reddedilen v0.2 jeneratöründe prob çalıştırılmadı; sol sütun eski pilot
jeneratörüyle yapılan tanıya aittir. v0.3'te tam özetin daha yüksek
doğruluğu, sıklık sinyali zayıflarken koşullu ortalamaların yararlı
olabileceği öngörüsüyle tutarlıdır; doğrudan nedensel doğrulama değildir.

Her probda 896 örtüşen test satırı ve yaklaşık 14 bağımsız pencere
uzunluğunda blok vardır. Bu yaklaşık sayı kesin etkin örneklem büyüklüğü
değildir. %65,4'ün şanstan ayrıldığı gösterilmemiştir; bu durum sıklıkların
bilgi taşımadığını da kanıtlamaz. Tam özetin %100 sonucu da aynı küçük
örneklem sınırıyla okunur. Ayrıca iki prob farklı akış tohumları kullandı;
fark eşleştirilmiş bir ablasyon değildir. 132 boyutun zorunluluğu veya
bilginin yalnızca koşullu ortalamalarda bulunduğu sonucu çıkarılmaz.

### Sonraki adım

Jeneratör kabul edildi. Önkayıt sırasına göre bundan sonrası: öğrenci
yapılandırmasının sabitlenmesi (bağlam biçimi, minibatch, sabit lr) →
kapı (20.000 örneklik dondurulmuş temiz doğruluk, ölçülen eşik bağımsız
kalibrasyon akışından, nominal bant %92,5–93,5) → kapı geçilirse M2
değerlendirmesi ve faz uzunluğu pilotu → dört faz. Bu adımlar bu turda
çalıştırılmadı.

---

Bu proje bir araştırma sonucunu kanıtlamaz. Sentetik akış, kâhin,
standart çevrimiçi öğrenme ve basit replay karşılaştırmasını çalıştırır.
Yönlendirme ve birim yenileme henüz yoktur.

## Çalıştırma

Komutları çalışma alanının kök dizinindeki terminalde çalıştırın.
Python, NumPy ve PyTorch gerekir; GPU gerekmez. Mevcut ortamda ek paket
yüklenmeden Python 3.13.2, NumPy 2.2.6 ve PyTorch 2.7.1 ile doğrulandı.

Ana uygulama: [pilot.py](pilot.py).
Testler: [test_pilot.py](test_pilot.py).

Test komutu:

    python -m unittest discover -s continual_pilot -p "test_*.py" -v

Kısa uçtan uca kontrol:

    python continual_pilot/pilot.py --phase-length 100 --health-length 100 --output continual_pilot/results_smoke

Kaydedilen pilotu yeniden üretme:

    python continual_pilot/pilot.py --phase-length 5000 --health-length 10000 --output continual_pilot/results_pilot

Seçenekleri görüntüleme:

    python continual_pilot/pilot.py --help

Aynı çıktı dizininde tekrar çalıştırmak önceki sonuçları değiştirir.
Yeni deneylerde farklı çıktı dizini kullanın. Aynı ortam ve tohumda
deterministik çalışma amaçlanır; süreler ve farklı platformlar arasında
sayısal sonuçlar birebir aynı olmak zorunda değildir.

## Deney düzeni

- Tohum 7, paylaşım katsayısı 0,5, simetrik etiket gürültüsü %5.
- Sekiz gizli faktör, ortonormal sütunlu dönüşümle 32 gözlenen boyuta taşınır.
- Gözlem gürültüsü yoktur. Öğrenci gizli faktörleri veya öğretmenleri görmez.
- Dört Gauss bileşeni ortaktır; yalnızca karışım ağırlıkları değişir.
- Ortak ve özgü küçük öğretmenlerin skorları toplandıktan sonra dört sınıftan biri seçilir.
- Fazlar: R1/M1 → R1/M2 → R2/M2 → R1/M2.
- Her faz 5.000 örnek; ayrı tek-rejim kontrolü 10.000 örnek.
- Öğrenci: 164 girdi, 64 gizli birim, dört çıktı; toplam 10.820 parametre.
- 164 girdi = 32 güncel ölçüm + 132 geçmiş bağlam özeti.
- Özet yalnızca son 64 etiketlenmiş örneğin sınıf sıklıkları ve sınıf-koşullu ortalamalarıdır.
- Her tahmin güncel etiket görülmeden yapılır. Faz sınırında öğrenci sıfırlanmaz.
- İki yöntem aynı başlangıç ağırlıklarını ve aynı gürültülü akışı kullanır.
- Adam öğrenme oranı 0,001; her yeni örnekte bir optimizasyon adımı.
- Replay: tüm geçmiş üzerinde uniform reservoir, kapasite 512.
- Replay güncellemesi bir yeni örnek ve en fazla sekiz geçmiş örnek içerir.
- Kayıp tüm bu örneklerin eşit ağırlıklı ortalamasıdır.
- Güncel örnek replay örneklemesinden ve güncellemeden sonra tampona girer.
- Replay örneği özgün tarihsel bağlamıyla saklanır; bağlam günümüze göre yeniden yazılmaz.
- Tek-rejim kontrolündeki modeller ana akışa taşınmaz; her koşu başlangıç modelinden başlar.

## Kaydedilen sonuçlar

Tam rapor: [summary.json](results_pilot/summary.json).
200 örneklik blok eğrileri: [curves.csv](results_pilot/curves.csv).

Pişmanlık, öğrencinin hata sayısından aynı gürültülü etiketlerde kâhinin
hata sayısının çıkarılmasıdır. Daha düşük değer daha iyidir.
Kâhin temiz kuralı bilir, rastgele etiket bozulmasını bilmez.

| Ölçüm | A | Replay |
|---|---:|---:|
| Faz 3, ilk 1.000 örnek pişmanlığı | 297 | 404 |
| Faz 4, ilk 1.000 örnek pişmanlığı | 173 | 163 |
| Faz 4, toplam 5.000 örnek pişmanlığı | 615 | 801 |
| Faz 4, tüm faz doğruluğu | %82,64 | %78,92 |
| Tek-rejim kontrolü, son 1.000 doğruluğu | %85,2 | %81,7 |
| Ana akış çalışma süresi | 10,39 sn | 12,04 sn |
| Kalıcı sayısal veri kapasitesi | 139.104 bayt | 479.072 bayt |
| Gradyanlar dahil sayısal veri kapasitesi | 182.384 bayt | 522.352 bayt |
| Eğitimde işlenen örnek, tekrarlar dahil | 20.000 | 179.964 |
| Yaklaşık doğrusal katman FLOP | 1,72 milyar | 12,04 milyar |

Dört koşunun ölçülen çevrimiçi döngü süreleri toplamı yaklaşık 33,61 saniyedir.
Bu toplam başlatma, jeneratör, dosya yazma ve test sürelerini içermez.

**Yorum:** Replay, geri dönüşün ilk penceresinde 10 hata avantaj sağladı,
ancak yeni kurala uyumu ve geri dönüş fazının toplamını kötüleştirdi.
Tek tohumda bu küçük fark istatistiksel veya mekanik yeniden kullanım
kanıtı değildir. Replay'in genel üstünlüğü gösterilmedi.

## Pilotun açığa çıkardığı sorunlar

1. Tek-rejim kontrolü yaklaşık %95 kâhin düzeyine yakınsamayı göstermedi.
   Yedi yazılım testi geçti; bu, öğrenilebilirlik kontrolünün geçtiği
   anlamına gelmez. Kapasite, optimizasyon, bağlam ve sonlu tampon etkileri
   ayrıca incelenmelidir; tek başına kod hatası sonucu çıkarılamaz.
2. M2 altında öğretmen uyuşmazlığı %73,78 oldu. Tartışılan %40–70
   örnek aralığına uymuyor; bu aralık pilotta zorlanmadı veya sonuçlara
   bakılarak yeniden ölçekleme yapılmadı.
3. Sınıflar dengeli değil. M1/R1 altında bir sınıfın payı %1,22;
   M2/R1 altında %3,44. Doğruluk bu dağılımlar bağlamında yorumlanmalıdır.
4. Geçmiş özetinin rejimi ayırt edebilmesi henüz bağımsız olarak sınanmadı.
5. Hipotez doğrulaması için koşuların ve jeneratörlerin çoğaltılması gerekir.
   Bu koşudan hareketle ayar seçilecekse bu veri pilot verisi olarak kalmalıdır.

## Maliyet ve kapsam sınırları

Aynı model ve veri kullanılır; toplam bellek ve hesaplama eşitlenmemiştir.
Replay'in ek kapasitesi 339.968 bayttır: 512 tarihsel özellik vektörü
ve etiket. Bağlam özeti bu maliyetin içindedir.

Bellek raporu açık sayısal veri muhasebesidir, süreç tepe belleği değildir.
Python nesneleri, rastgelelik durumlarının nesne yükü, aktivasyonlar,
geçici eğitim grupları, kütüphaneler ve değerlendiricinin önceden ürettiği
akışlar raporlanan kapasiteye dahil değildir. Bağlam için tam pencere
kapasitesi sayılır. Tepe bellek eşitliği veya cihaz enerji tasarrufu iddia edilmez.

FLOP yalnızca yoğun doğrusal katmanlar için yaklaşık ileri/geri geçiş
hesabıdır; aktivasyon, Adam ve bakım işlemlerini kapsamaz. Çalışma süresi
ise çevrimiçi tahmin, bağlam, tampon ve güncelleme işlemlerini kapsar.
Replay'in vektörleştirilmiş küçük grupları nedeniyle FLOP oranı süre
oranına eşit değildir.

Henüz uygulanmayanlar: yönlendirme, yenileme, yakın komşu rakibi,
değişim dedektörü, kural-naif geçmiş, eşik tabanlı tasarruf oranı,
plastisite probu, ablasyon, güç analizi ve güven aralıkları.
Bu teslim tam önkayıt uygulaması değil, çalışır ilk pilot kapsamındadır.

## v0.2 birleşik koşu (bağlamsız + 40k + minibatch 16)

Uygulama: [`diagnose_v02.py`](diagnose_v02.py), testleri
[`test_diagnose_v02.py`](test_diagnose_v02.py), sonuçları
[`results_v02/summary.json`](results_v02/summary.json).
Mevcut [`pilot.py`](pilot.py) ve [`diagnose.py`](diagnose.py) değişmedi;
dört fazlı deney yeniden çalıştırılmadı. Üç kalibrasyon kontrolünü
(bağlamı kaldır, daha çok örnek, daha az gürültülü adım) tek aday olarak
birleştirmek meşrudur; bu, faktör başına nedensel ayrıştırma değildir.
**29 test geçti.** Tek tohum, keşif amaçlı; anlamlılık testi değil.

Çalıştırma:

    python continual_pilot/diagnose_v02.py

### Kapı tanımı

Kapı metriği: 20.000 örneklik ayrı akışta **dondurulmuş temiz doğruluk**.
Eşik, değerlendirme akışından **bağımsız** bir kalibrasyon akışında
ölçülen çoğunluk sınıfı tabanından hesaplanır:
taban + 0,9 × (1 − taban). Çoğunluk sınıfı %42,1 olduğundan eşik
**%94,21** çıkar. Dengesiz jeneratörde eşiğin yükselmesi beklenendir.
Wilson %95 aralığı eşiği kesiyorsa sonuç belirsiz sayılır.

### Sonuçlar

| Kontrol | Bağlam | Örnek | Adım | Dondurulmuş temiz | Wilson %95 |
|---|---|---:|---:|---:|---|
| Referans | Var | 10.000 | 10.000 | %88,31 | [%87,85, %88,74] |
| Birleşik | Yok | 40.000 | 2.500 | %93,59 | [%93,24, %93,92] |

**Kapı kararı: BAŞARISIZ.** Birleşik koşunun Wilson üst sınırı (%93,92),
eşiğin (%94,21) altında. Belirsiz değil, kesin başarısız.

**Eşleştirilmiş bootstrap** (aynı değerlendirme akışında, tek model
standart hatası kullanılmadan): birleşik, referanstan örnek başına
**0,053 daha az hata** yapıyor (fark CI [−0,057, −0,049], negatif =
birleşik lehine). İyileşme gerçek ve eşleştirilmiş testle doğrulandı,
ama kapıyı geçmeye yetmiyor.

### Öğrenme eğrisi: plato + adım-gürültü değiş tokuşu

1.000 örneklik bloklarda çevrimiçi temiz doğruluk 5.000 örnekte %91,8'e
çıkıyor, sonra 40.000'e kadar ~%92–94 bandında dalgalanarak platoya
oturuyor; belirgin bir yükseliş yok. Birleşik koşu 40.000 örnekten yalnızca
**2.500 optimizasyon adımı** üretti (minibatch 16). Yani "daha az ama daha
az gürültülü adım" ile "daha çok adım" birbirini kısmen götürüyor; bu bir
adım sayısı–adım gürültüsü değiş tokuşudur, optimizasyon hipotezinin
çürütülmesi değildir. Plato, darboğazın kapasite değil temsil/optimizasyon
tarafında olduğunu destekliyor.

### Nadir sınıf darboğazı

M1/R1 değerlendirmesinde sınıf destekleri dengesiz (yaklaşık %23, %1,2,
%42, %34). Sınıf 1 geri çağırımı referansta %11,6, birleşikte %14,6;
karışıklık matrisi bu sınıfın çoğunlukla sınıf 2 ve 3'e karıştığını
gösteriyor. Neredeyse öğrenilemeyen bu %1,2'lik sınıf, %93,59 ile %94,21
arasındaki farkı tek başına fazlasıyla açıklıyor. Dengesizlik gerçek
darboğazdır; bu da jeneratör dengesinin ayrı bir sürümde çözülmesi
gerektiğini doğruluyor.

### Özet probu (gürültülü etiket, öğrencinin gördüğüyle aynı)

Aynı girdi dağılımında (M2) R1/R2 ayrımı: tam 132-boyutlu özet %95,9,
yalnızca 4 sınıf sıklığı **%100**. Yani rejim bilgisi neredeyse tümüyle
4 boyutta taşınıyor; 132-boyutlu tam özetin geri kalanı bu görevde gereksiz.
Pencereler örtüştüğü için 896 ham satır bağımsız gözlem değildir; tahmini
bağımsız blok sayısı ~14 olarak raporlanmıştır.

### Karar

Kapı geçilmedi. Sonraki adım, önceden kararlaştırıldığı gibi **v0.2
jeneratörü**: ortak bileşenin gerçek karışım dağılımında kalibre edilmesi
ve önceden sabitlenmiş kabul ölçütü (her sınıf ≥ %15, uyuşmazlık hedef
aralıkta). Kapı orada yeniden denenecek. Yönlendirme ve yenileme için
hâlâ erken. Kapı geçilseydi dört faza dönmeden önce M2'de dondurulmuş
temiz doğruluk da raporlanacaktı; geçilmediği için bu adım ertelendi.
Bütün ayarlar önceden belirlenmiş kontrollerdir, sonuca bakılarak
seçilmemiştir.

## v0.2 önkayıt spesifikasyonu (kod yazılmadan sabitlendi)

Bu bölüm, v0.2 jeneratörü ve kapısı için sonuçlara bakılmadan sabitlenen
kararları içerir. Henüz uygulanmadı; kabul raporu ve kapı sonucu ayrıca
eklenecektir.

### Nadir sınıf vurgusunun düzeltilmesi

v0.2 birleşik koşuda nadir sınıf tek başına vurgulanmıştı; bu abartılıydı.
Toplam 1.282 hatanın yalnızca ~%15'i (199) sınıf 1'e ait. Hata kütlesinin
büyük kısmı **sınır hatalarında**: 0↔2 (329 + 180) ve 3→2 (192). Dengeyi
düzeltmek kapıyı geçirebilir, ama plato (%93 bandı) esas olarak sınır
hatalarından gelir ve bu kısım dengeyle çözülmez. Bu nedenle kapı v0.2'de
geçilmezse "sorun dengeydi" denemez.

### Kapı öğrencisi = faz öğrencisi (bağlayıcı kısıt)

Kapıyı geçiren öğrenci yapılandırması ile dört fazda koşacak öğrenci
**aynı** olmalıdır; aksi hâlde "öğrenilebilir" dediğimiz şey fazda koşan
şey değildir. Özellikle:

- Öğrenme oranı **sabit** kalır. Plato için öğrenme oranı söndürme
  tek-rejimde kapıyı geçirse bile dört fazda plastisiteyi öldürür ve
  sabit-lr sürekli öğrenmeyle uyumsuzdur; bu yüzden yasaktır.
- Minibatch seçimi kapı öncesinde ve fazdan bağımsız olarak sabitlenir,
  fazda değiştirilmez. Tek kısıt: faz geçişindeki 1.000 örneklik pencerede
  kaç güncelleme düştüğü raporlanır (minibatch 16 için ~62). Seçim bu sayı
  görülerek değil, önceden yapılır.

### Öğrenci sabitleme sırası

Prob bulgusu v0.2'ye taşınmaz; bağlam kararı yeniden ölçülür. Prob bir
jeneratör tanılamasıdır, öğrenme koşusu değildir; bu yüzden "öğrenci
kapıdan önce sabitlenir" kuralını bozmaz. Sıra:

1. Jeneratör kabulü (aşağıdaki deterministik prosedür).
2. Prob (tam özet ve 4-sıklık) — jeneratör tanılaması.
3. Öğrenci yapılandırması sabitlenir (bağlam biçimi, minibatch, sabit lr).
4. Kapı denenir.

### Deterministik kabul-örneklemesi

- Öğretmen tohumları önceden sabit bir diziden sırayla denenir
  (seed, seed+1, …); **ilk kabul edilen** alınır.
- Denenen ve reddedilen tohum sayısı raporlanır.
- Üst sınır **200 deneme**; aşılırsa jeneratör tasarımı başarısız sayılır
  ve sürüm numarası değişir (kriter gevşetilmez).
- Ortak bileşen kalibrasyon örneklemi M1 ve M2'den **eşit oranda** alınır;
  eğitim, kalibrasyon ve değerlendirme akışlarından bağımsız tohumla.

### Denge kabul ölçütü (eşiği belirler)

Denge kriteri kapı eşiğini belirlediğinden alt ve üst sınır **birlikte**
yazılır. Nominal hedef: her sınıf payı **%18–%35**. Bu bandın sonucu,
nominal eşik aralığı:

- Dört sınıf eşit (%25): eşik = 0,25 + 0,9 × 0,75 = **%92,5**.
- Üst uç (bir sınıf %35): eşik = 0,35 + 0,9 × 0,65 = **%93,5**.

Yani bant kapıyı **nominal %92,5–%93,5** aralığına kilitler.

**Nominal vs ölçülen ayrımı:** Yukarıdaki bant nominaldir. Gerçek eşik,
kabul edilen jeneratörün nominal payından değil, **bağımsız kalibrasyon
akışında ölçülen** çoğunluk payından hesaplanır; örnekleme gürültüsüyle
bant birkaç binde kayabilir. Raporda bant "nominal", gerçekleşen eşik
"ölçülen" olarak ayrı yazılır.

Kriter yalnızca R1/M1'e değil, **R1 ve R2'ye, M1 ve M2 altında** uygulanır;
aksi hâlde faz 3–4 dengesiz kalır. Kural uyuşmazlığı hedef aralığı
(**%40–70**) da red kriterine dahildir. Bu kısıtların hepsi tek bir tohumun
kabulü için birlikte sağlanmalıdır.

### Kapı geçilmezse: önceden karar ağacı

Başarısızlıkta koldan kola atlamayı engellemek için üç okuma önceden
ayrıştırılır:

1. **Beklenen şekil — jeneratör kolu:** Hata kütlesi hâlâ sınır
   hatalarında **ve** sınıf başına geri çağırım hepsinde ≥ ~0,8 ise, sorun
   öğretmen keskinliğidir (jeneratör), öğrenci değil.
2. **Denge yetersiz:** Bir sınıfın geri çağırımı hâlâ çökükse, denge
   kriteri yeterli değildir.
3. **Süre/adım sorunu:** Hata dağınıksa ve plato yoksa (eğri hâlâ
   yükseliyorsa), sorun süre/adım sayısıdır.

"Beklenen hata şekli" birincisidir. Karışıklık matrisi ve hata kütlesinin
dağılımı v0.2'de de raporlanır; bu ağaç sonuçlara bakılmadan sabitlenmiştir.

### Prob bulgusu taşınmaz

4-sıklık probunun %100 vermesi, iki kuralın sınıf marjinallerinin M2
altında farklı olmasından kaynaklanır. Denge kriteri bu marjinalleri
yakınlaştırırsa 4-sıklık sinyali zayıflar ve tam özetin diğer kısımları
gerekli hâle gelebilir. Bu nedenle özet küçültme kararı v0.2 jeneratöründe
**yeniden ölçülmeden** verilmez. Ayrıca 132-boyutun 4-boyuttan düşük
çıkması (%95,9 vs %100) ~14 bağımsız blokla doğrusal probun aşırı uyumudur;
özetin bilgi taşımadığı anlamına gelmez. "Geri kalanı gereksiz" ifadesi
bu yüzden geri çekilmiştir.

### Değerlendirme büyüklüğü notu

Referansın dondurulmuş temiz doğruluğu 5.000 örneklik değerlendirmede
%89,24 iken 20.000 örneklikte %88,31 çıktı — aynı model, yaklaşık 2 standart
hatalık fark. Bu, kapı kararı için 20.000 örneklik değerlendirmeye geçişin
gerekli olduğunu doğrular.

## v0.2 jeneratör kabulü: tasarım başarısızlığı

Uygulama: [`generator_v02.py`](generator_v02.py), testleri
[`test_generator_v02.py`](test_generator_v02.py), sonuçları
[`results_generator_v02/summary.json`](results_generator_v02/summary.json).
Mevcut [`pilot.py`](pilot.py), [`diagnose.py`](diagnose.py) ve
[`diagnose_v02.py`](diagnose_v02.py) değişmedi; dört fazlı deney
çalıştırılmadı. **37 test geçti.**

Çalıştırma:

    python continual_pilot/generator_v02.py

### Yapılan değişiklik

Önkayıt spesifikasyonundaki ana düzeltme uygulandı: ortak bileşenin ölçeği
artık N(0,1) yerine **gerçek karışım dağılımında** (M1 ve M2'den eşit
oranda) kalibre ediliyor. Pilot jeneratörde ortak bileşenin girdisi
z[:, :2], ortalamaları (±1, ±1) olan bir karışımken kalibrasyon N(0,1)
kullanıyordu; bu uyumsuzluk giderildi. Diğer tüm mekanik (ortonormal
izdüşüm, additif ortak/özgü öğretmenler, simetrik %5 etiket gürültüsü)
korundu.

### Deterministik kabul sonucu: BAŞARISIZ

Tohumlar 1000'den başlayarak sırayla denendi; her tohum için kabul ölçütü
(her sınıf payı %18–%35, R1 ve R2 altında, M1 ve M2 altında; uyuşmazlık
%40–70) bağımsız bir metrik akışında ölçüldü. **200 denemenin hiçbiri
kabul edilmedi.** Önkayıt kuralı gereği bu bir tasarım başarısızlığıdır;
kriter gevşetilmedi.

### Teşhis: darboğaz tamamen sınıf dengesizliği

200 red kaydının analizi:

| Ölçüt | En düşük | Medyan | En yüksek |
|---|---:|---:|---:|
| En küçük sınıf payı | %0,33 | %7,75 | %17,6 |
| En büyük sınıf payı | %33,1 | %41,2 | %50,9 |
| M1 uyuşmazlığı | %58,4 | %67,9 | %77,8 |
| M2 uyuşmazlığı | %57,4 | %67,8 | %78,3 |

- **Denge ölçütünü tek başına sağlayan aday: 0/200.** Adayların en küçük
  sınıf paylarının en yükseği %17,6'dır. Tablodaki %33,1 ise adayların en
  büyük paylarının en düşüğüdür; aynı tohuma ait oldukları gösterilmedi.
- **Uyuşmazlık ölçütünü tek başına sağlayan aday: 150/200.** 150 aday
  yalnızca dengeden, 50 aday hem dengeden hem uyuşmazlıktan reddedildi.

Denge tüm adaylarda başarısız olan kısıttır; ancak uyuşmazlık ihlalleri
de vardır. 200 deneme matematiksel imkânsızlığı veya kesin geometrik nedeni
kanıtlamaz. Düzeltilen tasarım tercihi, dar bantlı 16 eşzamanlı koşulu
yalnızca rastgele aday arayışına bırakmaktır. Denge kalibrasyonla inşa
edilmeli, bağımsız kabul ölçümü korunmalıdır. Bu açıklama önceki
"tohum rastgeleliğiyle çözülemez" ve kesin neden ifadelerinin yerine geçer.

### Karar: sürüm artışı gerekli

Önkayıt karar ağacı gereği kriter gevşetilmez; **jeneratör tasarımı
değişmeli ve sürüm numarası artmalı (v0.3)**. Dengeyi yapısal olarak
sağlayacak bir değişiklik gerekir; örneğin sınıf sınırlarını `argmax`
yerine dengeli eşiklerle tanımlamak veya bileşen ortalamalarını/karar
kuralını sınıf paylarını hedefleyecek biçimde yeniden tasarlamak. Bu
tasarım kararı ayrı bir önkayıt turu gerektirir; sonuçlara bakılarak
kriter oynatılmayacaktır. Kapı, öğrenci sabitleme ve dört faz bu başarısız
jeneratörle denenmedi.

**Not:** Bu bölümdeki prob sonuçları yalnızca kabul edilen bir jeneratör
olsaydı raporlanacaktı; jeneratör reddedildiği için prob çalıştırılmadı ve
pilot prob bulgusu hâlâ v0.2'ye taşınmıyor.

## Başlangıç eşleştirmesi düzeltilmiş tanı

Yeni rapor: [`summary.json`](results_diagnose_init_fixed/summary.json).

20 test geçti. Tanı referansı ile özgün pilotun tek-rejim A koşulunun
10.000 tahmini bit düzeyinde eşit; farklılık 0. Uzun koşunun ilk
10.000 tahmini ile referans da bit düzeyinde eşit; farklılık 0.
Her iki dizinin SHA-256 özeti:
63ee24a2561eedbe627959f37fec391b46624410928c9250afb29edefa45101e.

| Kontrol | Çevrimiçi gürültülü doğruluk | Dondurulmuş temiz doğruluk |
|---|---:|---:|
| Referans | %84,49 | %89,24 |
| Bağlamsız | %86,36 | %91,44 |
| Gizli 128 | %84,26 | %88,96 |
| Gizli 256 | %84,02 | %88,94 |
| Minibatch 16 | %82,61 | %90,50 |
| Uzun 40k, bağlamlı | %86,47 | %91,98 |

Bu revizyon yalnızca başlangıç eşleştirmesini düzeltir.
Aynı şekilli modeller aynı başlangıcı alır; farklı şekillilerde aynı
tohum kullanılması parametre eşitliği anlamına gelmez. Dört faz yeniden
çalıştırılmadı. Yeni bir kapı kararı veya nedensel teşhis verilmedi.
Eski temiz-etiket probu bu revizyonda hâlâ korunmaktadır; rapordaki
%100 prob sonucu gürültülü öğrenci bağlamı için doğrulama değildir.
Replay tanısı, sınıf bazlı ölçümler, eğriler ve v0.2 bu revizyonun dışındadır.

## Arşiv — eski tek-rejim tanısı (yorumları geri çekildi)

**Aşağıdaki bölüm tarihsel kayıt olarak korunmaktadır, geçerli teşhis
değildir.** Başlangıçlar eşleştirilmemişti; prob temiz etiket kullanıyordu.
“Bağlam zararlı”, “kapasite darboğaz değil” ve kesin jeneratör nedeni
iddiaları geri çekildi. Eski %92 kapı kararı da ölçüt değişikliği nedeniyle
geçerli değildir. Eski sonuç dosyasının üzerine yazılmadı.

Öğrenilebilirlik darboğazını bulmak için ayrı bir tanı yazıldı:
[diagnose.py](diagnose.py), testleri [test_diagnose.py](test_diagnose.py),
sonuçları [results_diagnose/summary.json](results_diagnose/summary.json).
Özgün [pilot.py](pilot.py) değiştirilmedi ve dört fazlı deney yeniden
çalıştırılmadı. Her kontrol referanstan yalnızca tek bir şeyi değiştirir;
tüm testler (16) geçtikten sonra kontroller yorumlanmıştır.

Çalıştırma:

    python continual_pilot/diagnose.py

Ölçüt, ağırlıkları dondurulmuş modelin ayrı bir tek-rejim değerlendirme
akışındaki temiz kural doğruluğudur. Değerlendirme akışı hiçbir güncellemeye
girmez; bağlam, bağımsız bir önceki geçmişten ısıtılır. Tek tohum,
keşif amaçlıdır; anlamlılık testi değildir.

| Kontrol | Tek değişiklik | Parametre | Optimizasyon adımı | Dondurulmuş temiz doğruluk |
|---|---|---:|---:|---:|
| Referans | — | 10.820 | 10.000 | %89,04 |
| Bağlamsız | Bağlam özeti kaldırıldı | 2.372 | 10.000 | %91,40 |
| Gizli 128 | Genişlik 128 | 21.636 | 10.000 | %88,94 |
| Gizli 256 | Genişlik 256 | 43.268 | 10.000 | %88,90 |
| Minibatch 16 | 16'lık gecikmeli güncelleme | 10.820 | 625 | %90,62 |
| Uzun 40k | Aynı akışın 40.000'e uzatımı | 10.820 | 40.000 | %91,92 |

Kâhinin temiz kural doğruluğu tanımı gereği %100'dür; değerlendirme
akışında gözlenen etikete karşı kâhin doğruluğu yaklaşık %95'tir.

**Teşhisler:**

1. **Bağlam özeti bu görevde zararlı.** Bağlamı kaldırmak dondurulmuş temiz
   doğruluğu %89,04'ten %91,40'a çıkardı ve parametreyi 10.820'den 2.372'ye
   düşürdü. Durağan rejimde 132 boyutluk özet sinyal katmıyor; her örnekte
   değişerek 32 gerçek sinyalin yanında gürültü işlevi görüyor.
2. **Kapasite darboğaz değil.** 128 ve 256 gizli birim referansı iyileştirmedi
   (%88,94 ve %88,90). Sorun ağın darlığı değil.
3. **Daha uzun eğitim ve seyrek güncelleme kısmen yardımcı.** 40.000 örnek
   %91,92'ye ulaştı; 16'lık minibatch yalnızca 625 adımla %90,62 verdi.
   Hiçbir tekil değişiklik önceden belirlenen %92 dondurulmuş temiz doğruluk
   hedefini net biçimde geçmedi.
4. **Bağlam özeti rejimi taşıyor.** Aynı girdi dağılımında (M2) R1 ve R2
   özetlerini ayıran doğrusal prob, bağımsız test akışında %100 doğruluk
   verdi. Bu, "replay durağan rejimde kötü çünkü farklı bağlamlar gürültü
   basıyor" açıklamasını doğrudan desteklemez: özet bilgi taşıyor. Ancak
   durağan tek-rejim kontrolünde bu bilgi yararsız olduğundan, özetin ağ
   için net gürültü davrandığı sonucu (teşhis 1) geçerliliğini korur.

**Jeneratör dengesi (yalnızca ölçüldü, değiştirilmedi):** Önerilen sınıf
başına ortalamadan arındırma dengeyi düzeltmedi. En küçük sınıf payı M1
altında %1,24 (debias öncesi %1,22) kaldı. Dengesizlik, öğretmen skorlarının
ortalama yanlılığından değil, gizli uzaydaki karar bölgelerinin
geometrisinden kaynaklanıyor; çözüm için farklı bir müdahale gerekir.
M2 altında kural uyuşmazlığı %73,3 ile hedeflenen %40–70 aralığının üzerinde.

**Karar:** Kapı testi hâlâ geçilmedi. Sonraki adımdan önce bağlam özeti
yeniden tasarlanmalı veya kaldırılmalı, jeneratör dengesi ve uyuşmazlığı
ayrı bir sürümde ele alınmalıdır. Yönlendirme ve yenileme eklemek için henüz
erken. Bu tanı ayarları da sonuç odaklı değil, önceden belirlenmiş
kontrollerdir; buradan seçilecek herhangi bir ayar pilot verisi sayılmalıdır.