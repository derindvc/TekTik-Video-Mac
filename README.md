# TekTık Video

TekTık Video, macOS üzerinde Chrome veya Edge ile çalışan bir video indiricisidir. Eklenti simgesine bastığında açık sayfanın adresi bilgisayarındaki yerel yardımcıya iletilir ve indirme başlar. Varsayılan kayıt yeri **Downloads → TekTik Video** klasörüdür.

## Mac kurulumu

1. [Kur-Mac.command](Kur-Mac.command) dosyasını aç. Terminal açılır; eksikse Homebrew üzerinden `yt-dlp`, Deno ve FFmpeg kurulur. Homebrew yüklü değilse [brew.sh](https://brew.sh) üzerinden kurup dosyayı yeniden aç. Kurulum yönetici yetkisi istemez; Homebrew kendi kurulumu sırasında isteyebilir. Mac'te video indirmeleri H.264/AAC kodlamalı MP4 dosyasına dönüştürülür; bu işlem indirme sonrasında biraz sürebilir.
2. Chrome'da `chrome://extensions`, Edge'de `edge://extensions` sayfasını aç ve **Geliştirici modu** seçeneğini etkinleştir.
3. **Paketlenmemiş öğe yükle** seçeneğiyle bu projenin içindeki **`extension`** klasörünü seç. TekTık Video simgesini araç çubuğuna sabitle.

macOS indirdiğin `.command` dosyasını engellerse Terminal'de proje klasörüne geçip `./Kur-Mac.command` çalıştırabilirsin. Kurulumdan sonra bu klasörü istediğin yerde tutabilirsin; eklenti yüklü kaldığı sürece `extension` klasörünü taşımaman gerekir.

## Kullanım

1. İndirme iznin olan bir videoyu aç ve araç çubuğundaki **TekTık Video** simgesine bas.
2. İlerlemeyi simge rozetinden takip et. Simgeye sağ tıklayıp **İndirmeleri göster** seçeneğini açarak durumu görebilir ve kayıt klasörüne gidebilirsin. Bir video veya video bağlantısına sağ tıklayarak da indirmeyi başlatabilirsin.

Bir bağlantıyı kopyaladıysan **İndirmeleri göster** ekranındaki alana yapıştırıp **MP3** veya **Video** seçerek indirebilirsin. YouTube Music şarkı bağlantıları ses dosyası olarak işlenir. yt-dlp'nin desteklediği erişilebilir SoundCloud ve Bandcamp parça bağlantıları da denenebilir; site desteği değişebilir.

Spotify'daki tek şarkı bağlantılarından da ses dosyası indirilemez. Uygulama bu bağlantılar için açıklayıcı bir hata gösterir; Spotify içeriğini çevrimdışı dinlemek için Spotify'ın kendi özelliğini kullan.

**İndirmeleri göster** ekranında sonraki indirmeler için kaliteyi, yalnızca ses (MP3) seçimini, en uzun video süresini ve kayıt klasörünü ayarlayabilirsin. Varsayılan seçim en iyi mevcut kalite, video ve ses, sınırsız süre ve Downloads klasörüdür. Süre sınırı seçildiğinde süresini bildirmeyen videolar da elenir. Video süresi ve tahmini kaynak boyutu biliniyorsa indirme satırında gösterilir. Son MP4 dosyası dönüşüm nedeniyle farklı büyüklükte olabilir.

Oturum isteyen bir sayfada sağ tıklayıp **Bu sitenin oturum çerezleriyle indir** seçeneğini kullanabilirsin. Tarayıcı yalnızca ilgili site için çerez erişimi ister. Çerezler o indirme için geçici dosyada tutulup işlem sonunda silinir. Bu yol her sitenin erişim hatasını çözmeyebilir.

YouTube video ve Shorts adresleri, doğrudan video dosyaları ve yt-dlp'nin desteklediği açık video sayfaları hedeflenir. YouTube desteği site değişikliklerinden etkilenebilir. Canlı yayınlar ve DRM korumalı içerikler kapsam dışındadır. Yalnızca indirmene izin verilen içerikleri indir. [YouTube Hizmet Şartları](https://www.youtube.com/t/terms)

İndirme bağlantısı yalnızca tıklama üzerine tarayıcıdan yerel yardımcıya aktarılır. Video kendi kaynağından indirilir. Eklenti geniş site izni istemez. İndirme geçmişinde video adresi yerine site adı, başlık, durum ve dosya bilgisi görünür. İndirme sürerken tarayıcıyı açık tut.

## Güncelleme ve kaldırma

- İndirmeler bittikten sonra `Kur-Mac.command` dosyasını yeniden çalıştır. Homebrew bileşenlerini ayrıca `brew upgrade yt-dlp deno ffmpeg` ile güncelleyebilirsin.
- Eklenti dosyaları değiştiyse uzantılar sayfasından **Yeniden yükle** düğmesine bas; açık **İndirmeler** sekmesini kapatıp tekrar aç.
- Yerel yardımcıyı kaldırmak için Terminal'de proje klasöründen `./Kur-Mac.command --uninstall` çalıştır, ardından tarayıcı uzantısını kaldır. İndirilen videolar silinmez.

## Lisans

Bu projenin kaynak kodu [MIT lisansı](LICENSE) ile yayımlanır. İndirilen videoların hakları kaynaklarına aittir.
