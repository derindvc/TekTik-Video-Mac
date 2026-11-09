# TekTık Video

TekTık Video, macOS ve Windows üzerinde Chrome veya Edge ile çalışan bir video indiricisidir. Eklenti simgesine bastığında açık sayfanın adresi bilgisayarındaki yerel yardımcıya iletilir ve indirme başlar. Videolar **İndirilenler → TekTik Video** klasörüne kaydedilir.

## Mac kurulumu

1. [Kur-Mac.command](Kur-Mac.command) dosyasını aç. Terminal açılır; eksikse Homebrew üzerinden `yt-dlp`, Deno ve FFmpeg kurulur. Homebrew yüklü değilse [brew.sh](https://brew.sh) üzerinden kurup dosyayı yeniden aç. Kurulum yönetici yetkisi istemez; Homebrew kendi kurulumu sırasında isteyebilir. Mac'te her video H.264/AAC kodlamalı MP4 dosyasına dönüştürülür; bu işlem indirme sonrasında biraz sürebilir.
2. Chrome'da `chrome://extensions`, Edge'de `edge://extensions` sayfasını aç ve **Geliştirici modu** seçeneğini etkinleştir.
3. **Paketlenmemiş öğe yükle** seçeneğiyle bu projenin içindeki **`extension`** klasörünü seç. TekTık Video simgesini araç çubuğuna sabitle.

macOS indirdiğin `.command` dosyasını engellerse Terminal'de proje klasörüne geçip `./Kur-Mac.command` çalıştırabilirsin. Kurulumdan sonra bu klasörü istediğin yerde tutabilirsin; eklenti yüklü kaldığı sürece `extension` klasörünü taşımaman gerekir.

## Windows kurulumu

Windows x64 üzerinde [Kur.bat](Kur.bat) dosyasını çalıştır. İlk seferde yt-dlp, Deno ve FFmpeg indirilir. Ardından Chrome veya Edge uzantılar sayfasında geliştirici modunu açıp `extension` klasörünü **Paketlenmemiş öğe yükle** ile seç.

## Kullanım

1. İndirme iznin olan bir videoyu aç ve araç çubuğundaki **TekTık Video** simgesine bas.
2. İlerlemeyi simge rozetinden takip et. Simgeye sağ tıklayıp **İndirmeleri göster** seçeneğini açarak durumu görebilir ve kayıt klasörüne gidebilirsin. Bir video veya video bağlantısına sağ tıklayarak da indirmeyi başlatabilirsin.

YouTube video ve Shorts adresleri, doğrudan video dosyaları ve yt-dlp'nin desteklediği açık video sayfaları hedeflenir. YouTube desteği site değişikliklerinden etkilenebilir. Giriş isteyen veya DRM korumalı videolar kapsam dışındadır. Yalnızca indirmene izin verilen içerikleri indir. [YouTube Hizmet Şartları](https://www.youtube.com/t/terms)

İndirme bağlantısı yalnızca tıklama üzerine tarayıcıdan yerel yardımcıya aktarılır. Video kendi kaynağından indirilir. Eklenti geniş site izni istemez. İndirme geçmişinde video adresi yerine site adı, başlık, durum ve dosya bilgisi görünür. İndirme sürerken tarayıcıyı açık tut.

## Güncelleme ve kaldırma

- Mac'te indirmeler bittikten sonra `Kur-Mac.command` dosyasını yeniden çalıştır. Homebrew bileşenlerini ayrıca `brew upgrade yt-dlp deno ffmpeg` ile güncelleyebilirsin. Windows'ta `Kur.bat` dosyasını yeniden çalıştır.
- Eklenti dosyaları değiştiyse uzantılar sayfasından **Yeniden yükle** düğmesine bas.
- Mac'te yerel yardımcıyı kaldırmak için Terminal'de proje klasöründen `./Kur-Mac.command --uninstall` çalıştır, ardından tarayıcı uzantısını kaldır. Windows'ta `.\Kur.bat -Kaldir` çalıştır. İndirilen videolar silinmez.

## Lisans

Bu projenin kaynak kodu [MIT lisansı](LICENSE) ile yayımlanır. İndirilen videoların hakları kaynaklarına aittir.
