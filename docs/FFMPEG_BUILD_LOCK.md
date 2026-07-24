# FFmpeg build lock

Status: READY FOR PROFESSIONAL LEGAL REVIEW

- Provider: BtbN/FFmpeg-Builds
- Provider release tag: autobuild-2026-06-30-13-34
- Provider commit: 7a83528ea3431e9eca982a712bc3a7cd0789d5d0
- Artifact: ffmpeg-N-125365-g9a01c1cb6a-win64-lgpl-shared.zip
- Artifact URL: https://github.com/BtbN/FFmpeg-Builds/releases/download/autobuild-2026-06-30-13-34/ffmpeg-N-125365-g9a01c1cb6a-win64-lgpl-shared.zip
- Artifact SHA-256: 52d25fc4711078112ba622d07601f183371af43e2d93cbb6e5eab3e1c05387cb
- FFmpeg version: N-125365-g9a01c1cb6a-20260630
- FFmpeg commit: 9a01c1cb6a
- FFmpeg source URL: https://github.com/FFmpeg/FFmpeg/archive/9a01c1cb6a.zip
- FFmpeg source SHA-256: 8ca7287b2659c2309ad5060caad5b9ae4ef51f1b54ed5a30e0bfc815ee1c376d
- Provider source URL: https://github.com/BtbN/FFmpeg-Builds/archive/7a83528ea3431e9eca982a712bc3a7cd0789d5d0.zip
- Provider source SHA-256: 14e560e13dea71189bd317be0b6c3fe5ba42b74c5a73a6b5952ddf44d5225e99

## Build configuration

```text
--prefix=/ffbuild/prefix --pkg-config-flags=--static --pkg-config=pkg-config --cross-prefix=x86_64-w64-mingw32- --arch=x86_64 --target-os=mingw32 --enable-version3 --disable-debug --enable-shared --disable-static --disable-w32threads --enable-pthreads --enable-iconv --enable-zlib --enable-libxml2 --enable-libvmaf --enable-fontconfig --enable-libharfbuzz --enable-libfreetype --enable-libfribidi --enable-vulkan --enable-libshaderc --enable-libvorbis --disable-libxcb --disable-xlib --disable-libpulse --enable-gmp --enable-lzma --enable-liblcevc-dec --enable-opencl --enable-amf --enable-libaom --enable-libaribb24 --disable-avisynth --enable-chromaprint --enable-libdav1d --disable-libdavs2 --disable-libdvdread --disable-libdvdnav --disable-libfdk-aac --enable-ffnvcodec --enable-cuda-llvm --disable-frei0r --enable-libgme --enable-libkvazaar --enable-libaribcaption --enable-libass --enable-libbluray --enable-libjxl --enable-libmp3lame --enable-libopus --enable-libplacebo --enable-librist --enable-libssh --enable-libtheora --enable-libvpx --enable-libwebp --enable-libzmq --enable-lv2 --enable-libvpl --enable-openal --enable-liboapv --enable-libopencore-amrnb --enable-libopencore-amrwb --enable-libopenh264 --enable-libopenjpeg --enable-libopenmpt --enable-librav1e --disable-librubberband --enable-schannel --enable-sdl2 --enable-libsnappy --enable-libsoxr --enable-libsrt --enable-libsvtav1 --enable-libtwolame --enable-libuavs3d --disable-libdrm --enable-vaapi --disable-libvidstab --enable-libvvenc --disable-whisper --disable-libx264 --disable-libx265 --disable-libxavs2 --disable-libxvid --enable-libzimg --enable-libzvbi --extra-cflags=-DLIBTWOLAME_STATIC --extra-cxxflags= --extra-libs=-lgomp --extra-ldflags=-pthread --extra-ldexeflags= --cc=x86_64-w64-mingw32-gcc --cxx=x86_64-w64-mingw32-g++ --ar=x86_64-w64-mingw32-gcc-ar --ranlib=x86_64-w64-mingw32-gcc-ranlib --nm=x86_64-w64-mingw32-gcc-nm --extra-version=20260630
```

## Binary hashes

| path | size | sha256 |
| --- | ---: | --- |
| bin/avcodec-63.dll | 70567424 | d4f475d7a5d9218def1010b019ba5ebc020cb3e795d58e655f1c114bcf11b2ea |
| bin/avdevice-63.dll | 3698688 | da768f25c28877cb046a50c4192da7cf6779571dd402d73c0f5244df0947d55d |
| bin/avfilter-12.dll | 29554176 | 1f046e83e2e2aecbe03711870401d70626e0fd48f93fdd21db092e2c42ca7087 |
| bin/avformat-63.dll | 21782016 | 9bf009456e78533dc6aa3d3591acb3fab45baf4e90da773f5947c129289ecaf3 |
| bin/avutil-61.dll | 2943488 | 3d92328446598f490e77ba7ece29c3efc42603f47b451020b4d624b2c3faa70b |
| bin/ffmpeg.exe | 543744 | 35b594d864ee183be60d71c5a0efadef958153ef3ff53fddb11fcb90d29b4f3f |
| bin/ffplay.exe | 17850368 | 35be3374c6b3f1beeac0c7bc2feb3b708944471ba6c7cd14da751b60578f2b55 |
| bin/ffprobe.exe | 232448 | e97c56926e443d144c0e56aa4a3f1bcc00762626e959efaa4d1ddd9cd20684c7 |
| bin/swresample-7.dll | 722944 | 7a4ed680ec138a7ee4d31a1957f9fe787eb6d53145ccf65bcdd9b6586ab6f439 |
| bin/swscale-10.dll | 12731392 | 3758abbb7bdc73808600b5bc606882f136a243bac00a6b67cc81edddec1b642f |
| doc/bootstrap.min.css | 109483 | 3cedecf2b8064b4a56ba47bda04544e1b21d71c83a12e7b5709e7c7976ead70e |
| doc/community.html | 13505 | ed1a149ca1f5129e31b71f7bf6547a690bbefed1f94b24d3b6cf15b9b5e7cac6 |
| doc/default.css | 2494 | 504c4a0980e6ec809da02ce16b73151622a2fdfb4409098c7ce96c1cac9b3735 |
| doc/developer.html | 65222 | c7dc5bbc7d5cbe775558e5db6a14a4b17e06a8589d19b4ee0d0b44d309920f8b |
| doc/drawvg-reference.html | 147341 | e63e3aa79935d162c5e29e8feac866ae899ae0073f45595b3a029b42a897db90 |
| doc/faq.html | 65088 | 12e4eaa685c874b975e9ad774aabd588871088a877f531ba2f7aa628b1670c45 |
| doc/fate.html | 18768 | 603ae75dc972d486d4901c222ec881d6bb903058311dfcc9cda9f6471c50e3aa |
| doc/ffmpeg-all.html | 3081464 | 9938b0bacad000a161b91a80b319f1620e575cac37c75fcad5998afb09609743 |
| doc/ffmpeg-bitstream-filters.html | 62913 | 6783e37c2cafaec9337ac5188d72d1722b539f5bff9c08a1542ae0ec32bfb545 |
| doc/ffmpeg-codecs.html | 348541 | 1e0c1482d7c0df446173268563f515dca6ed6dedf62b114a834d04ecb8aecfa9 |
| doc/ffmpeg-devices.html | 112837 | 4cbeaf4948a0c267ea4de2f8bdaae49b169bd7d1a69202a4cf71fe79d9deb1a5 |
| doc/ffmpeg-filters.html | 1691524 | 28e81129b40d37e70df68e7f1e059ca23cc2bcf62791df7152b22b6edfb8401c |
| doc/ffmpeg-formats.html | 337768 | cca9e45d496e2a43fae86454d3d79cb3c5b53e80638d8c351cf1728755ba44f1 |
| doc/ffmpeg-protocols.html | 122313 | 2c13f0a9320f1088d785a6d223333fa58132b99e16c44eeef73ff950fffde04a |
| doc/ffmpeg-resampler.html | 13818 | ef33b5c00313e980fd8bef875e48ad49534f8d4da3acd62c2cb121cf2f767986 |
| doc/ffmpeg-scaler.html | 13074 | fae13e4c728490df237c2690327cacc5e22581c5e952fc429b706dd841028414 |
| doc/ffmpeg-utils.html | 55775 | f0acb1ad146da71c65450b975f6e7e102eed03ee40eb9163e5d7b70df2e82146 |
| doc/ffmpeg.html | 217190 | 55652233f15f468e2ecfd8af15571de2f7aedc676110882e38a003c5fd968b41 |
| doc/ffplay-all.html | 2379408 | a77e2b419ae4dc217a133aff968891694979e825bb2f19f0975d1662392574fc |
| doc/ffplay.html | 42145 | c94ff755a36c9028aeeaf93f853df75450c23962a7bea43b6ae0177684195c37 |
| doc/ffprobe-all.html | 2395843 | 0989fd5525e71afc0b2ad224fa99b9a724324289a73de9a8f36c3aa1f40081b4 |
| doc/ffprobe.html | 58506 | ca1dead6f3c6b93f6245ce6be3101ca2e176c69c768579a8d0d2383b57884763 |
| doc/general.html | 129043 | 0da20102efcc3435badffbe91d57672d3e41e459dc7122d583def2778be970dd |
| doc/git-howto.html | 27737 | e44ed6484fa73f819c59494c68be232728319250bd86c6e32a760ddca620e108 |
| doc/libavcodec.html | 3147 | faf8dd1ae157374e92a685970fa28f21e0df8a2dfb8c3ea99e58d6d956bee879 |
| doc/libavdevice.html | 3026 | cea441629a753d099d8b1032f0814a87cfa113d830f8fcdebd047738cb5481ac |
| doc/libavfilter.html | 3092 | d02ec4ed1dddb7cb09f9c4e9f2bf38810b3050f6db5f839f398bd6561cab4322 |
| doc/libavformat.html | 3122 | 49f9fdced269207bfd3a6bcb63738b3f1dcf2b3c7641eba509fd46f37c5cebcc |
| doc/libavutil.html | 3621 | ba59342959874520f152b8df5eedde47295929a43e29646392e03c6fcdc2d8e9 |
| doc/libswresample.html | 4005 | f66d2d2e5f29ba56f47d2855d5cd8f276bf207241d024a5a06d0564b96d52bf5 |
| doc/libswscale.html | 3621 | 41859c7b95dd3d1089e2189c2dc81b1da920557e66ec181a1f8fe04dcc829118 |
| doc/mailing-list-faq.html | 31209 | e6a26273f248a5ca7f4354fc8b19e4d0bceeefc3c7aa492db58072fdc9e6a944 |
| doc/nut.html | 11231 | 97706cef7a10c32fa781aca5242443868c003858c84b41629e7c04d77b2b0d0c |
| doc/platform.html | 22177 | 8d6c71e3d28c52cddd7de85fcdbbdd87d22a02fa9905a6b3169ff9767033fd6d |
| doc/style.min.css | 6523 | 02496d7bdbd48d0f332dc94b62668906cbeabc3a8592253d5dfe2e5196522660 |
| include/libavcodec/ac3_parser.h | 1207 | 200c6d2e96975196e8ba5f5716223dc9dda999d51578dabce2fca93175a05252 |
| include/libavcodec/adts_parser.h | 1354 | d466583a8dc1260b015e588adbe3abd45f3f8ca0e43722f3088b472e80492a15 |
| include/libavcodec/avcodec.h | 108600 | 324452903f0d3b4bb4078652ca32c9ca29d7b3db5e005e1af04487409bd3090d |
| include/libavcodec/avdct.h | 2767 | c13d581750798e92f6d93e5903fbfdf81ee3a3b56003cbb2683f95d87e84b725 |
| include/libavcodec/bsf.h | 11540 | cc26676aa44638fa5cbef953d967e19e2084b46aaa100f0a35ba2d34b302301c |
| include/libavcodec/codec.h | 11788 | ad4550b3f8ff7c7dd1c79a373721ba43273c4d1f156c683e11e27f9b5d89be1a |
| include/libavcodec/codec_desc.h | 4264 | d1fc6e89a3a7e49e61893620e00256d4f00db994764435ebe159b46a3c4326b5 |
| include/libavcodec/codec_id.h | 18573 | 765765fee16f9551ebd4fb5441fc6e5fc3d93c4754703831673bf887f2b1c87d |
| include/libavcodec/codec_par.h | 8400 | c33270179f2d44d94a75438923400f6a1c6dacf7b755692e723e3101cbeb65d3 |
| include/libavcodec/d3d11va.h | 2610 | 0a5b324124f3dd67942bac8d8288aba152215fb0ef2dede40d492198e0989346 |
| include/libavcodec/defs.h | 13333 | f1d391ac2417702b59b7a4b6ae3927eea8c8b5e9858ae9ade6fdd009a60bd9ce |
| include/libavcodec/dirac.h | 4126 | 09fd1f670422ee61713568abd90fdf371b30e6fe35bc6fb8213f1ad32b45cf56 |
| include/libavcodec/dv_profile.h | 3694 | 19f59e0b20ac583de4bfd76d18889d334bf0b6cdf7b5356723a33f3874738466 |
| include/libavcodec/dxva2.h | 2128 | 3a603c2cf8bc00d0c9df6cc80a5f0ed091d48d20303713baac1c7e432619f0bb |
| include/libavcodec/exif.h | 8430 | f3305bce9777fe9bafdb6abf2b90ebdd9c3b17a4149b33002d8c22d1c4d9a6d3 |
| include/libavcodec/jni.h | 2263 | f98405ffb7ba26665cde92daef33bc4371c91aa6c85b522b36864ed289600ebc |
| include/libavcodec/mediacodec.h | 3570 | 1f64544000dd2f2ec94604d5fcf7c2a6d26d32d085264356084a4b53a7f0c3f0 |
| include/libavcodec/packet.h | 32798 | 2e10c19c2fd953a5f18198eea1106334254d963f86df7999857c293dee8ac056 |
| include/libavcodec/qsv.h | 3844 | e45780237ab0e9ea9ec11aab9f62dfb8b059138f846632ecacdc024db16dfb1b |
| include/libavcodec/smpte_436m.h | 11580 | 6e5a93aad21b7c098fb8ac5d1e4ba469887f8cfce0eb21762b35c2fd1097f2a8 |
| include/libavcodec/vdpau.h | 4555 | 014ec822b00aa33305d503ea128c04287e7d1265194fda3a91cc00cd2a763272 |
| include/libavcodec/version.h | 1619 | c5d42bc34cbc4f95af14c95e53be0921513d1ebef9adf69ecd5d6efae4723cc4 |
| include/libavcodec/version_major.h | 1629 | 4ce6f0974cff7069900045ee551001bb57902a2f5ec0b5f538fbc1e4e9f6aa83 |
| include/libavcodec/videotoolbox.h | 2445 | b182be72a4404f99dc761680193f647c47c2a792ab50d975f6d8b75984c6f5b9 |
| include/libavcodec/vorbis_parser.h | 2285 | 57077b2e1d28d42636cab0f69e4b92b1ad64ac2eaa2843c270a6afaf308a76ae |
| include/libavdevice/avdevice.h | 13506 | a4d649615eeab8d4c2cf882a6dd06be4a95f74a1f6cf18d6ea819186c2d60ac3 |
| include/libavdevice/version.h | 1624 | cc0d869e638cdb053122ee8988318635f9b18a76ced0cd3e1327571d8affc9f2 |
| include/libavdevice/version_major.h | 1200 | 0efd5fa8f843690041e388e98a0acd53a37ae3129bfb0f8a8aa6d4798caa43b8 |
| include/libavfilter/avfilter.h | 45670 | c80d2ee378b654c9bafbd466a762201fd894093420005ec24effe6b145debbac |
| include/libavfilter/buffersink.h | 6979 | 72c8ae2993837c280cfdf176db13cf7dfaec6b0aec3fb81a899037083c62e2be |
| include/libavfilter/buffersrc.h | 7227 | 8f4131e9c38aff4ef8c0dd6b736a47f7601adeaf49344d48effa41c02b5f9745 |
| include/libavfilter/version.h | 1653 | 0f34d3f35e0b8e002964d830df2233c495a3a55562eae03e445627bc07e91014 |
| include/libavfilter/version_major.h | 1223 | 1e25372ff02d13346c534159d48d965e67cee1caa63400dc5074e76fe0bdb222 |
| include/libavformat/avformat.h | 121793 | 694da025f30497481f4703e06de106bd417a5718f8fdcdf5e09e34f4b5f21114 |
| include/libavformat/avio.h | 31178 | 30312971fc299e65bc69cf1beddb76f50394e044d9c71fe32fec3ae9c13bd1af |
| include/libavformat/version.h | 1652 | 70fc05235520c8ef1adcef496a4ceeb02265bf919697c9bd9b36bd0c481fa6cc |
| include/libavformat/version_major.h | 1876 | 436db6c1b56db87e83682639fd0285e8b0138acc4fb572868c70a690eda7bb5e |
| include/libavutil/adler32.h | 1696 | f21a861957bf4b1812ed67fdc528890f9cff1bb483facf0f5109e4a51932fe3b |
| include/libavutil/aes.h | 1912 | 0a86ebeaf9ed33548bf0f92359f7047e521d4d80fe6b0ef1c8ef9505e38b6d28 |
| include/libavutil/aes_ctr.h | 2443 | fbbb94888bfab2ea7141e7e1afa5872de099e7ee57baea17632c3d4fdd2cba3f |
| include/libavutil/ambient_viewing_environment.h | 2585 | 00135de08089f8c711bb113588f80575a1d26e86d50b6dac5928a27a0ff9a8c7 |
| include/libavutil/attributes.h | 6672 | 041300e50a7e4c97d5ab3ea8c92d3db637e7047c8cb021f64ead2874391ee954 |
| include/libavutil/audio_fifo.h | 5966 | 3c513ca46927346c0673cd9db302afe62dbbf976844f36da0307fd10f7f47bfd |
| include/libavutil/avassert.h | 4015 | 986182bd395e6559ec1a20243e540018ac99a64f1cd148f203ab6fbc4878f3ac |
| include/libavutil/avconfig.h | 180 | 975611ad5eba15212d9e1d5fca9d4fdf0daec6d2269b2fcab8e29af8667164bc |
| include/libavutil/avstring.h | 14962 | 630d231013e996b10b2c9aec98c569f8f88dc53a425491d435d868172a53ecb0 |
| include/libavutil/avutil.h | 8702 | 01a511d927eaab20cf57076611ff5649bc6089d2d766c4b20c9d11c3da095efd |
| include/libavutil/base64.h | 2285 | 81ac13d23f3744fe85ea2651ce903e201cd55fc63fcdd899d2cfe5560d50ef3d |
| include/libavutil/blowfish.h | 2394 | b955a63c60c8b3be0203ec6c3973f9084d848cf884fe56cd56088301aeef7992 |
| include/libavutil/bprint.h | 8818 | 5e3800d797fb8f67ffa7917420d3710c759afaca6f84b655fb64bf4dfa4650d2 |
| include/libavutil/bswap.h | 2788 | 1d985324139f195d3247c3bb59aa7976c074fbaaf85b8b783f88c178c59f48d3 |
| include/libavutil/buffer.h | 11998 | f16742d574216434580573a2b09f56fc5b66b7dda1960d4f02ba59e3269ba548 |
| include/libavutil/camellia.h | 2139 | 1db30753e71c73f1937e807850069e8215cdf37a1bc3ff89d3a6370a719c1fde |
| include/libavutil/cast5.h | 2561 | 05b2e13aecaa0adbb470081a689f45baffb8e03a71997c31f37a22ea4e383a60 |
| include/libavutil/channel_layout.h | 34091 | fbd3246297cd72be45268eacd9229d23247dfe394fb15b6a40ce8773422661c6 |
| include/libavutil/common.h | 17359 | 08f14cf0ea3fede141d3790b30df2ed6edfc5dd81eb3c8181c3a33c314c46bbb |
| include/libavutil/container_fifo.h | 4855 | d8bbe3f1f4dfcdcd56f40618961736ff3bc34fafd81f52ac6c993c91ef43916a |
| include/libavutil/cpu.h | 6857 | 52034bd08c5fa7b476451acb4578152bfd88e650774a92c107c810e820314063 |
| include/libavutil/crc.h | 3259 | 5728cf65705a46723ea28b4f6c8361aad82b76a90e859943efe8af0edb79ec86 |
| include/libavutil/csp.h | 7304 | 2760b91454642f77f88339f39b614da987c806b30ea54b6f6eddb1a7ac3a738e |
| include/libavutil/des.h | 2514 | 15ebdda1af65d91c4607a3444c5f749d5e9757ff5d7f4b04213b3194603f74d9 |
| include/libavutil/detection_bbox.h | 3524 | 8f5817d77af243a52e905947aa5ae73c218d68dba909040b2f63bd2ca6f93922 |
| include/libavutil/dict.h | 9521 | b8b7abebb6e5ab5ffa70b8463df52c96d4e774aa2d5574bebbc02f6031e62ad8 |
| include/libavutil/display.h | 3472 | b9c78c80aa9331b945802b6bcd1db4ecc9ec4f9fad41993cc82b880c0dec2576 |
| include/libavutil/dovi_meta.h | 12730 | e0ca4be00b203f35ceff50b53c92f448450c823eb24df7f01db0cd0d6c9077cb |
| include/libavutil/downmix_info.h | 3235 | 2fc23ad8f0750d82fcd6aa3b653998e2ea9721f9d1664df7b6cb80e93d7fa3aa |
| include/libavutil/encryption_info.h | 7056 | ccc3a4a889b8a3c5aaf37b9fb2407bcdf23a065487c7cba718518a517c463b18 |
| include/libavutil/error.h | 5555 | bcf4f7e69c7e0d658ad6e81611810f7cf1f0b8334ebe948d27e518c459e4104c |
| include/libavutil/eval.h | 6600 | 68efeaa9b6600ec47dae9031d1f0869818c88083b24fb133de3c2cf73f8adf1f |
| include/libavutil/executor.h | 1924 | db578edacd55adbb7be49ff6662777f3ddb84f530e0ad7d7cd8e0c18f0aae878 |
| include/libavutil/ffversion.h | 208 | ff92fe982961ab4104b5e51781ebfb528d6d5b83b8aef0338c532c4704a40cfc |
| include/libavutil/fifo.h | 8487 | 9d6e9a6db887d32ee3f4bdafab68869d00f9d89590e33718922c37067eb7f5fe |
| include/libavutil/file.h | 2225 | 10daa0d0f1f2a3bedf2b7d8b5c4fea208dd9cf8caabb81dac341fc6ad24f685f |
| include/libavutil/film_grain_params.h | 9190 | 414d2755769a6993d0c3f4b5a7e92e22a558675f0c49b44df3afc876473e825c |
| include/libavutil/frame.h | 43901 | 2eb83475589dbe72d9dbbb5367370b7c1384fbb20afffbcf482de0437b6eaf8e |
| include/libavutil/hash.h | 8457 | b0896571267220736679eea28c454783795a02a0f1aef008ebe7c40489a75fdd |
| include/libavutil/hdr_dynamic_metadata.h | 18320 | a33138bdb7eea6c7895c8daa2cfcdf6eec5bea0774d40f4d62051426ddab8678 |
| include/libavutil/hdr_dynamic_vivid_metadata.h | 8427 | 91580e9f4eb39ef296365aa756ef48a170b57c07b288be4bb10affd98ede83f2 |
| include/libavutil/hmac.h | 2865 | d14d625a897d6bba0668acdf33dc597bb0050237c5c1a5f7e568fe36822782e7 |
| include/libavutil/hwcontext.h | 24170 | 229c918d0809dbbaa0aaebd18848bece039ad458538f0fcafc11015fd2111fc2 |
| include/libavutil/hwcontext_amf.h | 2217 | ce2775092bba5f8b5b24d281394487bcf89ba560eb115547bfe43f0698bca8b9 |
| include/libavutil/hwcontext_cuda.h | 1843 | 4878f46347271bc7a9ff26bb1573449a99cc81447684e1034a3edd4b0ff91d9a |
| include/libavutil/hwcontext_d3d11va.h | 7193 | ac6ffe37fb89e9b935c2654cebd931f78972b960cd16406dfe9cc2b80869eef9 |
| include/libavutil/hwcontext_d3d12va.h | 6201 | 62c67ab00795c6a521801d3ac32e9e09180982958130d3737a48f38d2db9d75b |
| include/libavutil/hwcontext_drm.h | 4673 | b598f37f40cf1342f923c0b97784a6f2830b543868eccee046375e096fbd5f24 |
| include/libavutil/hwcontext_dxva2.h | 2411 | 73a0333b65e99675834dcb1b63a5e9339638ccc619f1a2fcba85cdd0e179ade0 |
| include/libavutil/hwcontext_mediacodec.h | 1988 | 8c602859ebca906ba6e43ea548ff28821cf2886b4500b2be1deaaf2d552496d4 |
| include/libavutil/hwcontext_oh.h | 1098 | 62df338901602b1ac41b8a61fb26b2179de39662e78f3e2b87b6464c53895ddc |
| include/libavutil/hwcontext_opencl.h | 3098 | c6e9ec709d824a24928e1dd9e5f80411b008657402320d6e02d149df83dc6c3c |
| include/libavutil/hwcontext_qsv.h | 2515 | 735168cd07100f41000e2cb4121786dcbd7d54fc12585b4682faae28f883d653 |
| include/libavutil/hwcontext_vaapi.h | 3784 | 5a63f50d3f1972b63038f03e005d53d8e666f119d8015f07038312c713aaf0f1 |
| include/libavutil/hwcontext_vdpau.h | 1360 | 6c96373d9e5deb2c500004f3f55ee1d2cea0f76cdfaeabaf5a3ad3e4938e8252 |
| include/libavutil/hwcontext_videotoolbox.h | 3877 | 71bbb6baf2dceff96c8673ef5afc5467548efb7b99c4d98d67df49c624f740c1 |
| include/libavutil/hwcontext_vulkan.h | 11870 | aeb211e2a4c97eac7fd2ff8908e57b075dc2a125f66a2fe47e770c8cf7cc2634 |
| include/libavutil/iamf.h | 21603 | c085745f71262d01c47f7c4eadbfd624cfd192056a87e4a83a9224e868c789ce |
| include/libavutil/imgutils.h | 16326 | 8e0055fd86fb10b7c9e435e9375736b6db201cb9930a38fb4ff1e1a1da8e0cff |
| include/libavutil/intfloat.h | 1726 | 3a29e4eebc8c269cfd867b96de91d8231773d392c12a8820e46eaba96d2b4ca1 |
| include/libavutil/intreadwrite.h | 19426 | 6e9c404e70f71a02208af81910434e47c501cbe1b0a80116e731cb673f98c734 |
| include/libavutil/lfg.h | 2542 | 6f094721480df57814cad6e6ce0f3f81867ffec24c58ee4d3e1800ec3484a061 |
| include/libavutil/log.h | 14088 | b8ef46be6210baadb3ad61eb72ee48e7dd7d6be39c17c3a8bbc8c81ba9e26110 |
| include/libavutil/lzo.h | 2048 | 61e89928dee9d83030adececac06aa6c1ae2aada06c5682fde52c52015c53556 |
| include/libavutil/macros.h | 2304 | b63b3a268b096f0eed1e91b821714cff334e5dc5bb34365148704393ae15321e |
| include/libavutil/mastering_display_metadata.h | 4284 | dbb1584931d4d8ff7d7a868b519097b6d92f0426d781543987cb784f80ba973a |
| include/libavutil/mathematics.h | 9565 | e85c71fb77b0fe7823a88db904982e2a9b953e806ced0714fe6cc6b8a0951469 |
| include/libavutil/md5.h | 2092 | 5b42de1758d289f78b4d20c47686f443e4ea8a5a6411c0deb357f709d2ef34d7 |
| include/libavutil/mem.h | 20457 | bf9a1d8c218c38b333efb16be076c5778d31d66a0691bdd6175f171c08283d7c |
| include/libavutil/motion_vector.h | 1770 | dc0b0a15a638c8b91df95a418c5951ee5e787d518f22b6e3d70094922536e8bb |
| include/libavutil/murmur3.h | 3507 | 649258a51c4737fa19a025a489e2ac9e9b06a96eafa802f2765178c684382887 |
| include/libavutil/opt.h | 46030 | ed473055a2c58dc24bc560d9c86dbbc51558c3e87836f1c0869011130783d999 |
| include/libavutil/parseutils.h | 7888 | e8efed69396851f429a8258d50e9c4f0431f921687a7c31bf6db13d14f7482c3 |
| include/libavutil/pixdesc.h | 16432 | 4dc17f708daedb294fd3aa7ec1940f4b9a504518b4d4813be83db605ac13494d |
| include/libavutil/pixelutils.h | 2051 | 339cd6ffb6460d06401801c5dfb91ca66b9bdc028e1acc9ff4a0f447cfd3785c |
| include/libavutil/pixfmt.h | 47890 | 6a8f5a61fe8d3bda60a62e59cc15237f61555ebd77adf477fc6d69ab8e609f77 |
| include/libavutil/random_seed.h | 1889 | 4490fd79919aadb18f765caac0c210d22cafa4d63cddcf9275e6f5bf66e2fdea |
| include/libavutil/rational.h | 6287 | f4fb850924b414f9ca35579df4e50d6f406734eb9735bbfbf388ae22ec5a0a9c |
| include/libavutil/raw_color_params.h | 4724 | 75710ebb3492d2d08734ac5530bca3b4ee60b614fb619aa50acd6da81e9f74c5 |
| include/libavutil/rc4.h | 2004 | 61b69b7bc0183b17e5d6e4a56e991fa2452bb97c0d4512c4b0d70b69656ee305 |
| include/libavutil/refstruct.h | 12172 | 8e7be80109d14fce52e3de7a30932efea283abe963ccdd755787e219a4699b19 |
| include/libavutil/replaygain.h | 1607 | 4ec82edbdc4e5493fba3cae6a27566f0f15d1399ccf16e25073ffd50ba8187ea |
| include/libavutil/ripemd.h | 2158 | df9ef8c29ee31e5bd8ea299b03d51bd25fe937583793a994db53d1df2b316620 |
| include/libavutil/samplefmt.h | 10270 | bec4e2708b42a026450c1227e137661f71850698f19b89f6e9f721fe993f56a9 |
| include/libavutil/sha.h | 2368 | 91280db6995b1b99b9e5aad0aa211a3177dc4d2841da2fea097f54964b7891fd |
| include/libavutil/sha512.h | 2413 | da265152798b221706d7fe95293a0e8cd18fa2b5087bf32504a8120f10e7658f |
| include/libavutil/spherical.h | 8607 | ab945689e58b593157d8532f315c8fb8674fb4c9f4ac96c1106a5aa62be8889d |
| include/libavutil/stereo3d.h | 7446 | 32cc28caac01b5bf18ae016af4b0ffffbe40feb77e96cb434d723954a83b776a |
| include/libavutil/tdrdi.h | 5280 | 9b7ac5326cadef9f3956470e22cdb9ba751c0da90b39f9df4562bffc8e4115a3 |
| include/libavutil/tea.h | 2035 | 3c1e93c566630bb4eeedad3ef3c8719bd6050081ac1c764b1fde81aba4969076 |
| include/libavutil/threadmessage.h | 3910 | 9bb242d7adc48662b947726843108aff7c34547d7a4a0d0e6f58f54a00fc4c9f |
| include/libavutil/time.h | 1800 | 40e11fa242e0585996753affb054443e78be25919b7c3063042d0aaff1656760 |
| include/libavutil/timecode.h | 7843 | 20936b639afa89e7a356bd5f5317b33745b1f4c3d467486ad043cb9b5d51527a |
| include/libavutil/timestamp.h | 2726 | dfd2e2071577f04ddc3cae200abd96ba0fb7d38f53359025af319d4b902f1947 |
| include/libavutil/tree.h | 5408 | 2f8e906917612a05c138036dea7ed9f8faee5899413a523fdad4eb51711bc1e5 |
| include/libavutil/twofish.h | 2245 | b71714336821e1c606b65620ba4b1ea47e431666be41f3174facbc51047fd814 |
| include/libavutil/tx.h | 7141 | a1c5c309f493cc22f4637e67696581be676cd33fdcaa0661a01f5bb4345c900a |
| include/libavutil/uuid.h | 4895 | e669ce76a6b987e189b4d7ff62d0fd9ad6e334fa4967076cc6d912976574b646 |
| include/libavutil/version.h | 4124 | 4ef5b1f1223ad72ca36c68a8991506a1ca708e54fff17dbcd6b698bc426a0ab2 |
| include/libavutil/video_enc_params.h | 5991 | f287486c4f828f82e579f93ea98fccb98749129544f660decfa56da6f818fd57 |
| include/libavutil/video_hint.h | 3585 | 7ae7b1e152aa7daf0ae55e29b1ed673039678d62d3f7a11d9c9443cfc8236997 |
| include/libavutil/xtea.h | 2834 | 2eb91f780cc4ad86095e4ebbce453475d40f4e9b8737d52bdf20a068dfafcdf0 |
| include/libswresample/swresample.h | 22361 | b23e625ab295d57a3d1ae0142c937b485dc386a36e4ed63f4b99ed886dc905e1 |
| include/libswresample/version.h | 1707 | f08b224d21834e867d47fdb43da25139ace7a16e53d5a6319af6bc3cfa7ebb21 |
| include/libswresample/version_major.h | 1015 | c730cced7041664f716e82872850329b59fa965f1c93044ce37593bd14a59c40 |
| include/libswscale/swscale.h | 29030 | 93ddab4bade7c0e1a59a5a33ef922532eafde42199999fc5fdc744163b83bdd3 |
| include/libswscale/version.h | 1589 | 2f170002f8dee766a0f0a06de0cb5721b0935efdbeb334ecc3e6728be3b73182 |
| include/libswscale/version_major.h | 1176 | b5981c7a57dda91c1b58aa9df212dd0214091f9d87448f2d86dac07f0ea17549 |
| lib/avcodec-63.def | 4732 | 99b91883edf050f52ae0cace705d4918cf866366a43d12e7bb8567857ddeb200 |
| lib/avcodec.lib | 143314 | c30950282317ff066c0499b270ea1bb013f69cc1d53e86c3d4c02fe490efd0fc |
| lib/avdevice-63.def | 453 | 4155c10e76c60ea96e0b9dc181b64e66fc0a4b2b699e492c87777ad221ef6eb5 |
| lib/avdevice.lib | 14120 | c406b8f6b4fd014ca36c39fa6e625f251f3235f9faccb5291431d6e51db78439 |
| lib/avfilter-12.def | 1973 | ee898f96b7994a1e35291e15841d41d6494832e8fab5aea94784d0deb1d23402 |
| lib/avfilter.lib | 57188 | 5cc9f91f3f133fb747c1c0d3e6cc9b8bab122b34fbe076d66f36e458de460664 |
| lib/avformat-63.def | 3584 | 502c13bba294ea6671ed13ce062e8e97f118cfcb8a73c7a78e9217fc38c2f7bb |
| lib/avformat.lib | 125962 | c0a1af9536ae42677d298edbc1bcb52a649199e2c2976ceb44058daefdb6bbca |
| lib/avutil-61.def | 15485 | 59ef857cf6227a990a685f21b70f97b321d82aaff756696539c999584131ba29 |
| lib/avutil.lib | 507098 | c3d1bb863fa33c6cc24b6f482e0c5a389c2c17838978391f3bc940adb7d4efdd |
| lib/libavcodec.dll.a | 119834 | 2b0f06223d41c232f682012e8a151de82a6c06a6263aa503f8e63e35dad0d169 |
| lib/libavdevice.dll.a | 11416 | 86f707bce33a2acc33ce987c6fd6915b9b0b428512f2ffbb7d415ce19b5f4913 |
| lib/libavfilter.dll.a | 47516 | f7f7773ce83466d948df0b98b850cb16da699c5beb838d60bb98d3c247524c6e |
| lib/libavformat.dll.a | 129012 | 9c344c1ed5046b293ce9e794e16feb617da36fd26e82860c8774e31aaf358496 |
| lib/libavutil.dll.a | 423906 | e2dc1533c77bb5e5d99793ea23d50ee735a2d4dea7fac8d1d15a4600f02ff49a |
| lib/libswresample.dll.a | 15964 | eaaeafe73c84ab48692157f2cebeb94e9f3280a5287d2f00c6628d926699acf0 |
| lib/libswscale.dll.a | 27362 | d0d5c6bf8ff3199b0dd91e9097fd17dfe37c55dae36c40dbb0b24fd482da7636 |
| lib/pkgconfig/libavcodec.pc | 310 | 9345b6d7cc65713ccc1740e4522467fd1fdd07cc327a8c1f355e3a7d1f6e6378 |
| lib/pkgconfig/libavdevice.pc | 420 | b3d24d6382dda2e770b00e35b32a76a5c309d11df873b24bcf8ce2b5a7341cad |
| lib/pkgconfig/libavfilter.pc | 401 | 838ac6ddcaafc82ebee32426061a84c084a5f9ac40798d70858b3e33a1c5de83 |
| lib/pkgconfig/libavformat.pc | 347 | 090861df0d2d471279f3b6238d36a6c8a1d59bdab30f17fe279116851ad26318 |
| lib/pkgconfig/libavutil.pc | 263 | ff1c77b3cd96c9d92c3ff97f6eb93b2ce58187cb820c21b0bb78aeb619f28c59 |
| lib/pkgconfig/libswresample.pc | 300 | b91f7f5d806a81f9ec5a4a2239f7c048936c3c52a3a4b8425857512bc9be41d1 |
| lib/pkgconfig/libswscale.pc | 294 | 1289f270a8ece8b3dfc76ec87e9e2ed3d83b307bc755e67d9853b51f49786d5c |
| lib/swresample-7.def | 475 | f9218bbdf6a09284adae3ef14e4b481a7a405d5a57de39907a6e803950114677 |
| lib/swresample.lib | 19876 | 91d4c4d737491b24ba57c48f93c7472985e9476f656db49f9335cc03754a4101 |
| lib/swscale-10.def | 911 | f99d273291bd67ecf4959e28cacad0b2d1ce67a4f6d318954cb389a1959bd8a1 |
| lib/swscale.lib | 33288 | b3603a09ce16695ab955d0650afa4801cf9c570fa20322f630f22f6476c1c72f |
| LICENSE.txt | 7651 | da7eabb7bafdf7d3ae5e9f223aa5bdc1eece45ac569dc21b3b037520b4464768 |
| MOVAURA_LOCK_SOURCE.json | 431 | 578f0285501926154a7938c7cc547e5276d7784624d7fcfae106e34954e6b265 |
| presets/libvpx-1080p.ffpreset | 227 | cf0dca9d029e0aa29c242e5a7ecfb202a55ae41c1acdf5e2e59bf281a0136251 |
| presets/libvpx-1080p50_60.ffpreset | 227 | 4d32bed9032caf8bf4ef8e4bcac427f482c6191396ef6b11f075a264da3a8def |
| presets/libvpx-360p.ffpreset | 219 | c2ccd70a941c9b7003e364d7cc0296e8f3dea78cc3a87ccdcaae7c39a1a05b79 |
| presets/libvpx-720p.ffpreset | 227 | 5bcac409c81ec0e11091801d5d1322b5ec6a9bb8617d7dda022acfea0d498d52 |
| presets/libvpx-720p50_60.ffpreset | 227 | b08a5ae448cb3cccd23faa6f42c8dbf61ead1a8381fce65636aa01a4a142cb8e |
