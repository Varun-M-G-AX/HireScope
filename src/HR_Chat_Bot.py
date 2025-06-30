import re
import streamlit as st
from datetime import datetime
from utils import collection, openai  # You must provide your own collection and openai setup

# Initialize sidebar state first
if 'sidebar_open' not in st.session_state:
    st.session_state.sidebar_open = True

# --- Bootstrap SVG Icons ---
ICONS = {
    "hirescope_logo": """<svg version="1.1" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 1042 1042"><path d="M0 0 C0.68429077 -0.00095673 1.36858154 -0.00191345 2.0736084 -0.00289917 C3.52286877 -0.0035808 4.97213218 -0.00172773 6.42138672 0.00244141 C8.64687928 0.00778998 10.87217001 0.0024959 13.09765625 -0.00390625 C14.50260461 -0.00324547 15.90755285 -0.0019643 17.3125 0 C18.59962891 0.00112793 19.88675781 0.00225586 21.21289062 0.00341797 C24.15625 0.1328125 24.15625 0.1328125 25.15625 1.1328125 C25.24920815 2.57571037 25.27371513 4.02311035 25.26977539 5.46899414 C25.26969986 6.3898732 25.26962433 7.31075226 25.26954651 8.25953674 C25.26438522 9.26056931 25.25922394 10.26160187 25.25390625 11.29296875 C25.2524913 12.31257187 25.25107635 13.33217499 25.24961853 14.38267517 C25.24400097 17.65358357 25.2314455 20.92442463 25.21875 24.1953125 C25.21373726 26.40690006 25.20917396 28.61848868 25.20507812 30.83007812 C25.1948748 36.26437002 25.17530285 41.69851548 25.15625 47.1328125 C38.35625 47.1328125 51.55625 47.1328125 65.15625 47.1328125 C65.14464844 43.82378906 65.13304687 40.51476562 65.12109375 37.10546875 C65.11330419 33.91512142 65.10722686 30.72477513 65.10131836 27.53442383 C65.09627683 25.31013518 65.08944377 23.08584987 65.08081055 20.86157227 C65.06873702 17.67202941 65.06302004 14.48253021 65.05859375 11.29296875 C65.05343246 10.29193619 65.04827118 9.29090363 65.04295349 8.25953674 C65.04287796 7.33865768 65.04280243 6.41777863 65.04272461 5.46899414 C65.040504 4.65402969 65.03828339 3.83906525 65.03599548 2.99940491 C65.15625 1.1328125 65.15625 1.1328125 66.15625 0.1328125 C68.36275656 0.03268849 70.57247386 0.0020007 72.78125 0 C73.44334473 -0.00095673 74.10543945 -0.00191345 74.78759766 -0.00289917 C76.18977961 -0.00358076 77.5919647 -0.00172792 78.99414062 0.00244141 C81.14720713 0.00779004 83.30006502 0.0024958 85.453125 -0.00390625 C86.81250046 -0.00324546 88.1718758 -0.00196429 89.53125 0 C91.39910156 0.00169189 91.39910156 0.00169189 93.3046875 0.00341797 C96.15625 0.1328125 96.15625 0.1328125 97.15625 1.1328125 C97.28061433 3.33805143 97.33432084 5.54728459 97.36157227 7.75585938 C97.3714662 8.45163684 97.38136013 9.1474143 97.39155388 9.86427593 C97.42338563 12.19333607 97.44806503 14.52241548 97.47265625 16.8515625 C97.49336451 18.48920664 97.51445385 20.126846 97.53590393 21.76448059 C97.59186423 26.14918296 97.64125505 30.53393553 97.68888092 34.9187355 C97.71860837 37.61994297 97.74997847 40.32112624 97.78192139 43.02230835 C98.02353159 63.49591593 98.25164886 83.97013085 98.28125 104.4453125 C98.2838382 105.28352539 98.28642639 106.12173828 98.28909302 106.98535156 C98.29476208 109.25981329 98.2935144 111.53413231 98.2890625 113.80859375 C98.28793457 115.02458252 98.28680664 116.24057129 98.28564453 117.4934082 C98.15625 120.1328125 98.15625 120.1328125 97.15625 121.1328125 C94.87677208 121.2330218 92.59417865 121.26362553 90.3125 121.265625 C89.62820923 121.26658173 88.94391846 121.26753845 88.2388916 121.26852417 C86.78963123 121.2692058 85.34036782 121.26735273 83.89111328 121.26318359 C81.66562072 121.25783502 79.44032999 121.2631291 77.21484375 121.26953125 C75.80989539 121.26887047 74.40494715 121.2675893 73 121.265625 C71.71287109 121.26449707 70.42574219 121.26336914 69.09960938 121.26220703 C66.15625 121.1328125 66.15625 121.1328125 65.15625 120.1328125 C65.06320982 118.65926902 65.03878735 117.18130659 65.04272461 115.70483398 C65.04283791 114.29348427 65.04283791 114.29348427 65.04295349 112.85362244 C65.04811478 111.83071609 65.05327606 110.80780975 65.05859375 109.75390625 C65.0600087 108.71210709 65.06142365 107.67030792 65.06288147 106.59693909 C65.0684992 103.25470156 65.0810547 99.91252993 65.09375 96.5703125 C65.09876272 94.31054784 65.10332602 92.05078213 65.10742188 89.79101562 C65.11762544 84.23823516 65.13719736 78.68559798 65.15625 73.1328125 C51.95625 73.1328125 38.75625 73.1328125 25.15625 73.1328125 C25.15625 88.9728125 25.15625 104.8128125 25.15625 121.1328125 C14.26625 121.1328125 3.37625 121.1328125 -7.84375 121.1328125 C-7.86629736 105.50402566 -7.88472937 89.87525164 -7.89556217 74.24645329 C-7.90072505 66.99022401 -7.90776758 59.73400554 -7.91918945 52.4777832 C-7.92913656 46.15547394 -7.93560349 39.83317249 -7.93783849 33.51085562 C-7.93914556 30.161245 -7.94223113 26.81165676 -7.94948006 23.4620533 C-7.9566862 19.72867605 -7.95774112 15.99534592 -7.95727539 12.26196289 C-7.96087067 11.14346954 -7.96446594 10.0249762 -7.96817017 8.87258911 C-7.9667955 7.86151596 -7.96542084 6.85044281 -7.96400452 5.80873108 C-7.96492631 4.92473161 -7.9658481 4.04073214 -7.96679783 3.1299448 C-7.68804761 -1.39432093 -3.67999368 0.00322483 0 0 Z " fill="#8B54FD" transform="translate(85.84375,459.8671875)"/><path d="M0 0 C0.7850441 -0.00960754 1.5700882 -0.01921509 2.37892151 -0.02911377 C3.64142982 -0.03548859 3.64142982 -0.03548859 4.92944336 -0.04199219 C6.24687782 -0.0505423 6.24687782 -0.0505423 7.59092712 -0.05926514 C9.45106813 -0.06870387 11.31122577 -0.07524464 13.17138672 -0.07910156 C15.98492653 -0.08874936 18.79771728 -0.1197591 21.61108398 -0.15136719 C44.79330752 -0.2889024 44.79330752 -0.2889024 53.46069336 6.65332031 C60.07153227 13.31594125 62.18605881 21.57207853 62.18310547 30.73925781 C62.17287354 31.49722656 62.1626416 32.25519531 62.15209961 33.03613281 C62.15008545 33.75542969 62.14807129 34.47472656 62.14599609 35.21582031 C62.13565038 37.86432409 62.10772928 40.51273589 62.08178711 43.16113281 C62.04053711 49.10113281 61.99928711 55.04113281 61.95678711 61.16113281 C42.48678711 61.16113281 23.01678711 61.16113281 2.95678711 61.16113281 C3.61678711 64.13113281 4.27678711 67.10113281 4.95678711 70.16113281 C8.10578609 71.21079914 10.05705882 71.21361556 13.34741211 71.07519531 C14.43948975 71.03193115 15.53156738 70.98866699 16.65673828 70.9440918 C18.41401245 70.8659021 18.41401245 70.8659021 20.20678711 70.78613281 C21.99983276 70.7127771 21.99983276 70.7127771 23.82910156 70.63793945 C27.53859665 70.48471532 31.24768426 70.3235502 34.95678711 70.16113281 C37.25755807 70.06323445 39.55833891 69.96556791 41.85913086 69.86816406 C47.22532331 69.63920869 52.5911717 69.40321991 57.95678711 69.16113281 C59.3544931 73.35425079 59.18081788 77.33158749 59.20678711 81.72363281 C59.22741211 82.59955078 59.24803711 83.47546875 59.26928711 84.37792969 C59.27702148 85.63379883 59.27702148 85.63379883 59.28491211 86.91503906 C59.29425781 87.68146729 59.30360352 88.44789551 59.31323242 89.23754883 C59.19560547 89.87233154 59.07797852 90.50711426 58.95678711 91.16113281 C55.29461458 93.60258117 52.20128984 93.70441284 47.94116211 94.01269531 C47.14137939 94.07677078 46.34159668 94.14084625 45.51757812 94.2068634 C42.91468581 94.41101213 40.31103905 94.60017866 37.70678711 94.78613281 C36.82430298 94.85083771 35.94181885 94.9155426 35.03259277 94.98220825 C-9.15178135 98.193358 -9.15178135 98.193358 -20.48071289 89.84863281 C-25.88530877 84.18039811 -28.13880732 78.58304302 -28.22021484 70.80102539 C-28.23305008 69.72923538 -28.24588531 68.65744537 -28.2591095 67.55317688 C-28.26649643 66.39899765 -28.27388336 65.24481842 -28.28149414 64.05566406 C-28.28956589 62.86188644 -28.29763763 61.66810883 -28.30595398 60.43815613 C-28.31978329 57.91052701 -28.3305106 55.38287931 -28.33837891 52.85522461 C-28.35556988 49.00565821 -28.39946595 45.15695554 -28.44360352 41.30761719 C-28.45373283 38.84863911 -28.46224818 36.38965375 -28.46899414 33.93066406 C-28.48650223 32.78660599 -28.50401031 31.64254791 -28.52204895 30.46382141 C-28.49690422 21.1165185 -26.26148027 13.67375588 -19.88696289 6.66503906 C-14.56886993 2.32718781 -6.81868205 0.06783912 0 0 Z M4.95678711 24.16113281 C2.21143112 28.9064888 2.21143112 28.9064888 2.95678711 38.16113281 C11.86678711 38.16113281 20.77678711 38.16113281 29.95678711 38.16113281 C29.95678711 34.20113281 29.95678711 30.24113281 29.95678711 26.16113281 C28.14910841 23.92981414 28.14910841 23.92981414 25.6184082 23.93408203 C24.18875732 23.94979248 24.18875732 23.94979248 22.73022461 23.96582031 C21.69897461 23.97226562 20.66772461 23.97871094 19.60522461 23.98535156 C17.98487305 24.01048828 17.98487305 24.01048828 16.33178711 24.03613281 C14.69983398 24.04966797 14.69983398 24.04966797 13.03491211 24.06347656 C10.34198559 24.08709872 7.64949456 24.12003725 4.95678711 24.16113281 Z " fill="#8C55FC" transform="translate(356.043212890625,486.8388671875)"/><path d="M0 0 C10.45269785 8.92641896 15.41157179 19.22297445 16.50537109 32.91503906 C17.34882675 50.00233313 16.78653829 66.25476537 5.2734375 80.01171875 C3.7884375 80.50671875 3.7884375 80.50671875 2.2734375 81.01171875 C2.2734375 81.67171875 2.2734375 82.33171875 2.2734375 83.01171875 C-5.68132048 89.74437704 -15.41133275 91.57869705 -25.5546875 91.29296875 C-34.64010049 90.48736563 -39.89464854 87.23299472 -47.7265625 82.01171875 C-48.0565625 96.53171875 -48.3865625 111.05171875 -48.7265625 126.01171875 C-56.9765625 126.01171875 -65.2265625 126.01171875 -73.7265625 126.01171875 C-73.7265625 83.11171875 -73.7265625 40.21171875 -73.7265625 -3.98828125 C-65.4765625 -3.98828125 -57.2265625 -3.98828125 -48.7265625 -3.98828125 C-48.3965625 -0.68828125 -48.0665625 2.61171875 -47.7265625 6.01171875 C-46.7365625 4.93921875 -45.7465625 3.86671875 -44.7265625 2.76171875 C-33.097173 -8.86767075 -13.17273065 -9.60590244 0 0 Z M-43.4765625 21.88671875 C-49.50105252 30.254066 -49.33112745 40.03090097 -48.7265625 50.01171875 C-47.61299508 56.57036782 -45.61478738 61.45678193 -40.7265625 66.01171875 C-35.20825096 69.25778436 -29.98189363 69.88296205 -23.7265625 69.01171875 C-19.20588153 67.6392307 -16.40371625 65.81361135 -13.3515625 62.19921875 C-10.05109555 55.72522588 -9.38560939 49.76137702 -9.4140625 42.63671875 C-9.39794922 41.8375 -9.38183594 41.03828125 -9.36523438 40.21484375 C-9.35947474 33.09592974 -10.67547802 26.3180123 -15.1015625 20.57421875 C-19.25998915 16.51480226 -22.93840364 15.72132554 -28.6640625 15.69921875 C-35.30839122 15.83764226 -38.81725324 17.01562271 -43.4765625 21.88671875 Z " fill="#030304" transform="translate(820.7265625,493.98828125)"/><path d="M0 0 C7.95069548 6.11312055 12.86860274 13.46924734 14.70703125 23.3125 C15.59337043 31.24998393 16.47096159 39.45499211 14.70703125 47.3125 C12.06988029 48.63107548 10.10870485 48.43241704 7.15576172 48.42602539 C5.99470917 48.42594986 4.83365662 48.42587433 3.63742065 48.42579651 C2.37906403 48.42063522 1.1207074 48.41547394 -0.17578125 48.41015625 C-1.46032196 48.4087413 -2.74486267 48.40732635 -4.06832886 48.40586853 C-7.48453717 48.40204911 -10.90070301 48.39222373 -14.31689453 48.38116455 C-17.80240301 48.37093807 -21.28791835 48.36636826 -24.7734375 48.36132812 C-31.6132987 48.35060096 -38.45313169 48.33353142 -45.29296875 48.3125 C-44.81791261 49.91971685 -44.34099252 51.52638283 -43.86328125 53.1328125 C-43.59789551 54.02758301 -43.33250977 54.92235352 -43.05908203 55.84423828 C-41.53088162 60.76779026 -39.98682111 63.21551399 -35.41796875 65.625 C-28.86286758 68.24490177 -21.66978339 68.49979001 -14.859375 66.65234375 C-9.69797921 64.39850173 -7.20340102 61.04195244 -4.29296875 56.3125 C0.23722478 56.86516686 3.14528039 58.64452985 6.89453125 61.1875 C7.93996094 61.88617187 8.98539063 62.58484375 10.0625 63.3046875 C12.70703125 65.3125 12.70703125 65.3125 14.70703125 68.3125 C8.65927482 78.5581109 1.38673737 86.02584184 -10.29296875 89.3125 C-24.43965789 92.19639806 -40.50890552 91.17146621 -52.79296875 83.0625 C-62.62176059 75.36898466 -68.95173081 65.68943425 -71.01171875 53.23046875 C-72.54534773 37.31906805 -71.49599769 22.01516436 -61.47265625 8.9375 C-46.94941618 -8.37648032 -19.03643257 -13.02696811 0 0 Z M-41.73046875 20.0625 C-43.80064386 23.92714718 -43.80064386 23.92714718 -44.29296875 31.3125 C-32.74296875 31.3125 -21.19296875 31.3125 -9.29296875 31.3125 C-9.99256309 22.01861432 -9.99256309 22.01861432 -15.29296875 15.5625 C-23.93881126 10.15884843 -35.2579206 12.76013799 -41.73046875 20.0625 Z " fill="#050505" transform="translate(922.29296875,494.6875)"/></svg>""",
    "chat": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path d='M2.678 11.894a1 1 0 0 1 .287.801 11 11 0 0 1-.398 2c1.395-.323 2.247-.697 2.634-.893a1 1 0 0 1 .71-.074A8 8 0 0 0 8 14c3.996 0 7-2.807 7-6s-3.004-6-7-6-7 2.808-7 6c0 1.468.617 2.83 1.678 3.894m-.493 3.905a22 22 0 0 1-.713.129c-.2.032-.352-.176-.273-.362a10 10 0 0 0 .244-.637l.003-.01c.248-.72.45-1.548.524-2.319C.743 11.37 0 9.76 0 8c0-3.866 3.582-7 8-7s8 3.134 8 7-3.582 7-8 7a9 9 0 0 1-2.347-.306c-.52.263-1.639.742-3.468 1.105'/></svg>""",
    "plus": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path d='M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4'/></svg>""",
    "three_dots": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path d='M3 9.5a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3m5 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3m5 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3'/></svg>""",
    "trash": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path d='M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0z'/><path d='M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4zM2.5 3h11V2h-11z'/></svg>""",
    "pencil": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path d='M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708L10.5 8.207l-3-3zm1.414 1.414-2.293 2.293L12.793 5.5zm-11.207 9.793L1 14l2.5-1.5 1.414-1.414L2.707 8.879z'/><path d='M10.5 1.5a.5.5 0 0 0-.5.5v.5h3a.5.5 0 0 1 .5.5v1A1.5 1.5 0 0 1 12 5.5H9.5a.5.5 0 0 1-.5-.5V4a.5.5 0 0 0-1 0v1.5A1.5 1.5 0 0 0 9.5 7h2.793l-3.793 3.793a.5.5 0 0 0-.146.353v.708c0 .193.084.377.229.518l1.25 1.25a.73.73 0 0 0 1.033 0l5.25-5.25a.5.5 0 0 0 0-.708L13.207 4.5H15.5a.5.5 0 0 0 .5-.5v-1a.5.5 0 0 0-.5-.5h-3V2a.5.5 0 0 0-.5-.5z'/></svg>""",
    "check": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path d='M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z'/></svg>""",
    "x": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path d='M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708'/></svg>""",
    "robot": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path d='M6 12.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3a.5.5 0 0 1-.5-.5'/><path d='M3 8.062C3 6.76 4.235 5.765 5.53 5.886a26.6 26.6 0 0 0 4.94 0C11.765 5.765 13 6.76 13 8.062v1.157a.93.93 0 0 1-.765.935c-.845.147-2.34.346-4.235.346s-3.39-.2-4.235-.346A.93.93 0 0 1 3 9.219zm4.542-.827a.25.25 0 0 0-.217.068l-.92.9a25 25 0 0 1-1.871-.183.25.25 0 0 0-.068.495c.55.076 1.232.149 2.02.193a.25.25 0 0 0 .189-.071l.754-.736.847 1.71a.25.25 0 0 0 .404.062l.932-.97a25 25 0 0 0 1.922-.188.25.25 0 0 0-.068-.495c-.538.074-1.207.145-1.98.189a.25.25 0 0 0-.166.076l-.754.785-.842-1.7a.25.25 0 0 0-.182-.135'/><path d='M8.5 1.866a1 1 0 1 0-1 0V3h-2A4.5 4.5 0 0 0 1 7.5V8a1 1 0 0 0-1 1v2a1 1 0 0 0 1 1v1a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-1a1 1 0 0 0 1-1V9a1 1 0 0 0-1-1v-.5A4.5 4.5 0 0 0 10.5 3h-2zM14 7.5V13a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V7.5A3.5 3.5 0 0 1 5.5 4h5A3.5 3.5 0 0 1 14 7.5'/></svg>""",
    "person": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path d='M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6m2-3a2 2 0 1 1-4 0 2 2 0 0 1 4 0m4 8c0 1-1 1-1 1H3s-1 0-1-1 1-4 6-4 6 3 6 4m-1-.004c-.001-.246-.154-.986-.832-1.664C11.516 10.68 10.289 10 8 10s-3.516.68-4.168 1.332c-.678.678-.83 1.418-.832 1.664z'/></svg>""",
    "menu": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path d='M2.5 12a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5m0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5m0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5'/></svg>""",
    "chevron_right": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path fill-rule='evenodd' d='M4.646 1.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708L10.293 8 4.646 2.354a.5.5 0 0 1 0-.708'/></svg>""",
    "chevron_left": """<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' viewBox='0 0 16 16'><path fill-rule='evenodd' d='M11.354 1.646a.5.5 0 0 1 0 .708L5.707 8l5.647 5.646a.5.5 0 0 1-.708.708l-6-6a.5.5 0 0 1 0-.708l6-6a.5.5 0 0 1 .708 0'/></svg>"""
}

# --- Custom CSS for Modern UI ---
st.markdown("""
<style>
/* Import modern fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* CSS Variables for Theme Support */
:root {
    /* Light theme colors */
    --bg-primary: #ffffff;
    --bg-secondary: #f8fafc;
    --bg-tertiary: #f1f5f9;
    --text-primary: #1f2937;
    --text-secondary: #374151;
    --text-tertiary: #6b7280;
    --border-color: #e5e7eb;
    --border-hover: #d1d5db;
    --accent-primary: #3b82f6;
    --accent-secondary: #22c55e;
    --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --gradient-secondary: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

/* Dark theme colors - Auto-detected */
@media (prefers-color-scheme: dark) {
    :root {
        --bg-primary: #0f172a;
        --bg-secondary: #1e293b;
        --bg-tertiary: #334155;
        --text-primary: #f1f5f9;
        --text-secondary: #e2e8f0;
        --text-tertiary: #94a3b8;
        --border-color: #475569;
        --border-hover: #64748b;
        --accent-primary: #60a5fa;
        --accent-secondary: #4ade80;
        --gradient-primary: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        --gradient-secondary: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
    }
}

/* Force dark theme for Streamlit dark mode users */
[data-theme="dark"] {
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --bg-tertiary: #334155;
    --text-primary: #f1f5f9;
    --text-secondary: #e2e8f0;
    --text-tertiary: #94a3b8;
    --border-color: #475569;
    --border-hover: #64748b;
    --accent-primary: #60a5fa;
    --accent-secondary: #4ade80;
    --gradient-primary: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
    --gradient-secondary: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
}

/* Global font settings */
* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
}

/* Code elements */
code, pre, .stCode {
    font-family: 'JetBrains Mono', 'Fira Code', 'Monaco', 'Cascadia Code', monospace !important;
}

/* Hide default Streamlit elements but keep system settings */
.stDeployButton {display: none;}
#MainMenu {visibility: visible !important;}
footer {visibility: visible;}
header[data-testid="stHeader"] {visibility: visible;}

/* Fix Streamlit layout issues */
.stMainBlockContainer {
    padding-top: 1rem;
    max-width: none !important;
    padding-left: 1rem;
    padding-right: 1rem;
}

/* Remove unwanted Streamlit margins and padding */
.block-container {
    padding-top: 1rem !important;
    max-width: none !important;
}

/* Fix sidebar width and spacing */
.stSidebar .block-container {
    padding-top: 2rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}

/* Remove Streamlit's default spacing */
.element-container {
    margin-bottom: 0 !important;
}

/* Fix button spacing */
.stButton {
    margin-bottom: 0.5rem !important;
}

/* Apply theme colors to main elements */
.stApp {
    background-color: var(--bg-primary);
    color: var(--text-primary);
}

.main .block-container {
    background-color: var(--bg-primary);
}

/* Improved typography with theme support */
h1, h2, h3 {
    font-weight: 600;
    letter-spacing: -0.025em;
    color: var(--text-primary) !important;
}

h1 {
    font-size: 2.25rem;
    line-height: 1.2;
}

h2 {
    font-size: 1.875rem;
    line-height: 1.3;
}

h3 {
    font-size: 1.5rem;
    line-height: 1.4;
    margin-bottom: 0.5rem;
}

/* Body text improvements with theme support */
p, div, span {
    font-weight: 400;
    line-height: 1.6;
    color: var(--text-secondary) !important;
}

/* Button improvements with theme support */
.stButton > button {
    font-weight: 500;
    font-size: 0.875rem;
    transition: all 0.2s ease;
    border-radius: 8px;
    border: 1px solid var(--border-color);
    box-shadow: var(--shadow-sm);
    background-color: var(--bg-primary);
    color: var(--text-primary);
}

.stButton > button:hover {
    border-color: var(--border-hover);
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
}

/* Primary button styling with theme support */
.stButton > button[kind="primary"] {
    background: var(--gradient-primary);
    border: none;
    color: white;
    font-weight: 600;
}

.stButton > button[kind="primary"]:hover {
    background: var(--gradient-secondary);
    box-shadow: var(--shadow-lg);
}

/* Fixed Sidebar Toggle Button - Only visible when sidebar is closed */
.sidebar-toggle-fixed {
    position: fixed !important;
    top: 1rem !important;
    left: 1rem !important;
    z-index: 9999 !important;
    background: var(--gradient-primary) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.75rem !important;
    cursor: pointer !important;
    box-shadow: var(--shadow-md) !important;
    transition: all 0.2s ease !important;
    font-weight: 600 !important;
    font-size: 1.1rem !important;
    min-width: 44px !important;
    min-height: 44px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

.sidebar-toggle-fixed:hover {
    background: var(--gradient-secondary) !important;
    transform: translateY(-1px) !important;
    box-shadow: var(--shadow-lg) !important;
}

/* Main content adjustment when sidebar is closed */
.main-content-adjusted {
    margin-left: 0 !important;
    padding-left: 80px !important;
}

/* Skeleton loading animation with theme support */
@keyframes skeleton-loading {
    0% {
        background-position: -200px 0;
    }
    100% {
        background-position: calc(200px + 100%) 0;
    }
}

.skeleton {
    display: inline-block;
    height: 1em;
    position: relative;
    overflow: hidden;
    background: linear-gradient(90deg, 
        rgba(255, 255, 255, 0.1) 25%, 
        rgba(255, 255, 255, 0.2) 50%, 
        rgba(255, 255, 255, 0.1) 75%);
    background-size: 200px 100%;
    animation: skeleton-loading 1.5s infinite;
    border-radius: 0.25rem;
}

@media (prefers-color-scheme: dark) {
    .skeleton {
        background: linear-gradient(90deg, 
            rgba(255, 255, 255, 0.05) 25%, 
            rgba(255, 255, 255, 0.1) 50%, 
            rgba(255, 255, 255, 0.05) 75%);
    }
}

/* Better loading states and animations */
.skeleton-container {
    padding: 1.5rem;
    margin: 1.5rem 0;
    border-radius: 12px;
    display: flex;
    gap: 1rem;
    align-items: flex-start;
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.05) 0%, rgba(21, 128, 61, 0.02) 100%);
    border: 1px solid rgba(34, 197, 94, 0.2);
    position: relative;
    overflow: hidden;
    transition: all 0.2s ease;
}

.skeleton-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: var(--accent-secondary);
    opacity: 0.8;
}

.skeleton-container:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}

.skeleton-icon {
    flex-shrink: 0;
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--accent-secondary) 0%, #16a34a 100%);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: var(--shadow-md);
}

.skeleton-content {
    flex: 1;
    line-height: 1.6;
}

.skeleton-line {
    margin: 0.5rem 0;
}

.skeleton-line:nth-child(1) { width: 90%; }
.skeleton-line:nth-child(2) { width: 85%; }
.skeleton-line:nth-child(3) { width: 70%; }
.skeleton-line:nth-child(4) { width: 95%; }

/* Thinking dots animation */
.thinking-dots {
    display: inline-flex;
    gap: 0.25rem;
    align-items: center;
    margin-left: 0.5rem;
}

.thinking-dot {
    width: 0.375rem;
    height: 0.375rem;
    border-radius: 50%;
    background: currentColor;
    opacity: 0.4;
    animation: thinking 1.4s infinite ease-in-out;
}

.thinking-dot:nth-child(1) { animation-delay: -0.32s; }
.thinking-dot:nth-child(2) { animation-delay: -0.16s; }
.thinking-dot:nth-child(3) { animation-delay: 0; }

@keyframes thinking {
    0%, 80%, 100% {
        opacity: 0.4;
        transform: scale(1);
    }
    40% {
        opacity: 1;
        transform: scale(1.2);
    }
}

/* Enhanced sidebar styling with better spacing */
.stSidebar > div {
    padding-top: 1rem;
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-color);
}

.stSidebar {
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-color);
}

/* Fix sidebar button spacing */
.stSidebar .stButton {
    margin-bottom: 0.75rem !important;
}

.stSidebar .stButton > button {
    width: 100% !important;
    text-align: left !important;
    justify-content: flex-start !important;
    gap: 0.5rem !important;
    font-weight: 500 !important;
    padding: 0.75rem 1rem !important;
}

/* Sidebar header improvements */
.stSidebar h3 {
    margin-bottom: 1rem !important;
    font-size: 1.25rem !important;
    font-weight: 600 !important;
}

/* Better sidebar section dividers */
.stSidebar hr {
    margin: 1.5rem 0 !important;
    border-color: var(--border-color) !important;
}

/* Sidebar text improvements */
.stSidebar .stMarkdown p {
    margin-bottom: 0.5rem !important;
    font-weight: 500 !important;
    color: var(--text-secondary) !important;
}

/* Chat item styling with theme support */
.chat-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem;
    margin: 0.25rem 0;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
    position: relative;
    border: 1px solid transparent;
    background-color: var(--bg-primary);
}

.chat-item:hover {
    background-color: var(--bg-tertiary);
    border-color: var(--border-color);
    box-shadow: var(--shadow-sm);
}

.chat-item.active {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
    border-color: var(--accent-primary);
    box-shadow: var(--shadow-md);
}

.chat-title {
    flex: 1;
    text-overflow: ellipsis;
    overflow: hidden;
    white-space: nowrap;
    font-size: 0.875rem;
    font-weight: 500;
    margin-right: 0.5rem;
    color: var(--text-primary);
}

.chat-actions {
    display: flex;
    gap: 0.25rem;
    opacity: 0;
    transition: opacity 0.2s ease;
}

.chat-item:hover .chat-actions {
    opacity: 1;
}

.icon-button {
    background: none;
    border: none;
    padding: 0.375rem;
    border-radius: 6px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
    color: var(--text-tertiary);
}

.icon-button:hover {
    background-color: var(--bg-tertiary);
    color: var(--text-primary);
}

/* New chat button with theme support */
.new-chat-btn {
    width: 100%;
    padding: 0.875rem;
    margin-bottom: 1rem;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    background: var(--bg-primary);
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.875rem;
    font-weight: 500;
    box-shadow: var(--shadow-sm);
}

.new-chat-btn:hover {
    background: var(--bg-tertiary);
    border-color: var(--border-hover);
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
}

/* Enhanced message styling with better spacing and readability */
.message {
    padding: 1.5rem;
    margin: 1.5rem 0;
    border-radius: 12px;
    display: flex;
    gap: 1rem;
    align-items: flex-start;
    border: 1px solid var(--border-color);
    box-shadow: var(--shadow-sm);
    background-color: var(--bg-primary);
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
}

.message::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: var(--accent-primary);
    opacity: 0.8;
}

.message.user {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(29, 78, 216, 0.02) 100%);
    border-color: rgba(59, 130, 246, 0.2);
}

.message.user::before {
    background: var(--accent-primary);
}

.message.assistant {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.05) 0%, rgba(21, 128, 61, 0.02) 100%);
    border-color: rgba(34, 197, 94, 0.2);
}

.message.assistant::before {
    background: var(--accent-secondary);
}

.message:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}

.message-icon {
    flex-shrink: 0;
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    box-shadow: var(--shadow-md);
}

.message.user .message-icon {
    background: linear-gradient(135deg, var(--accent-primary) 0%, #1d4ed8 100%);
    color: white;
}

.message.assistant .message-icon {
    background: linear-gradient(135deg, var(--accent-secondary) 0%, #16a34a 100%);
    color: white;
}

/* Improved message content with better typography */
.message-content {
    flex: 1;
    line-height: 1.7;
    font-size: 0.925rem;
    color: var(--text-secondary);
    word-wrap: break-word;
    overflow-wrap: break-word;
}

.message-content strong {
    font-weight: 600;
    color: var(--text-primary);
    font-size: 0.9rem;
    margin-bottom: 0.5rem;
    display: block;
}

.message-content p {
    margin: 0.75rem 0 !important;
    line-height: 1.7 !important;
}

.message-content ul, .message-content ol {
    margin: 0.75rem 0 !important;
    padding-left: 1.5rem !important;
}

.message-content li {
    margin: 0.25rem 0 !important;
    line-height: 1.6 !important;
}

.message-content code {
    background: var(--bg-tertiary) !important;
    padding: 0.2rem 0.4rem !important;
    border-radius: 4px !important;
    font-size: 0.85rem !important;
    border: 1px solid var(--border-color) !important;
}

.message-content pre {
    background: var(--bg-tertiary) !important;
    padding: 1rem !important;
    border-radius: 8px !important;
    border: 1px solid var(--border-color) !important;
    overflow-x: auto !important;
    margin: 1rem 0 !important;
}

.message-content blockquote {
    border-left: 3px solid var(--accent-primary) !important;
    padding-left: 1rem !important;
    margin: 1rem 0 !important;
    font-style: italic !important;
    color: var(--text-tertiary) !important;
}

/* Rename input styling with theme support */
.rename-input {
    width: 100%;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 0.375rem 0.75rem;
    color: var(--text-primary);
    font-size: 0.875rem;
    font-weight: 500;
    transition: all 0.2s ease;
}

.rename-input:focus {
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    background: var(--bg-primary);
}

/* Sidebar toggle button styling with theme support */
.sidebar-toggle-btn {
    background: var(--gradient-primary) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.625rem !important;
    cursor: pointer !important;
    box-shadow: var(--shadow-md) !important;
    transition: all 0.2s ease !important;
    font-weight: 600 !important;
    display: flex !important;
    align-items: center !important;
    gap: 0.5rem !important;
    font-size: 0.875rem !important;
}

.sidebar-toggle-btn:hover {
    background: var(--gradient-secondary) !important;
    transform: translateY(-1px) !important;
    box-shadow: var(--shadow-lg) !important;
}

/* Input styling improvements with theme support */
.stTextInput > div > div > input {
    border-radius: 8px !important;
    border: 1px solid var(--border-color) !important;
    padding: 0.75rem 1rem !important;
    font-size: 0.875rem !important;
    transition: all 0.2s ease !important;
    background: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

.stTextInput > div > div > input:focus {
    border-color: var(--accent-primary) !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
}

/* Improved chat input container */
.stChatInput {
    position: sticky !important;
    bottom: 0 !important;
    background: var(--bg-primary) !important;
    padding: 1rem 0 !important;
    margin-top: 2rem !important;
    border-top: 1px solid var(--border-color) !important;
    z-index: 100 !important;
}

/* Chat input styling with theme support */
.stChatInput > div {
    border-radius: 12px !important;
    border: 2px solid var(--border-color) !important;
    box-shadow: var(--shadow-md) !important;
    background: var(--bg-primary) !important;
    transition: all 0.2s ease !important;
}

.stChatInput > div:focus-within {
    border-color: var(--accent-primary) !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1), var(--shadow-lg) !important;
}

.stChatInput input {
    font-size: 0.925rem !important;
    font-weight: 400 !important;
    padding: 1rem 1.25rem !important;
    color: var(--text-primary) !important;
    background: transparent !important;
    border: none !important;
    line-height: 1.5 !important;
}

.stChatInput input::placeholder {
    color: var(--text-tertiary) !important;
    opacity: 0.8 !important;
}

/* Send button styling */
.stChatInput button {
    background: var(--gradient-primary) !important;
    border: none !important;
    border-radius: 8px !important;
    color: white !important;
    padding: 0.75rem !important;
    margin: 0.25rem !important;
    transition: all 0.2s ease !important;
    box-shadow: var(--shadow-sm) !important;
}

.stChatInput button:hover {
    background: var(--gradient-secondary) !important;
    transform: translateY(-1px) !important;
    box-shadow: var(--shadow-md) !important;
}

/* Better mobile responsiveness */
@media (max-width: 768px) {
    .message {
        padding: 1rem;
        margin: 1rem 0;
        gap: 0.75rem;
    }
    
    .message-content {
        font-size: 0.875rem;
    }
    
    .chat-title {
        font-size: 0.8rem;
    }
    
    .main-content-adjusted {
        padding-left: 60px !important;
    }
    
    h1 {
        font-size: 1.875rem !important;
    }
    
    .sidebar-toggle-fixed {
        top: 0.5rem !important;
        left: 0.5rem !important;
        padding: 0.5rem !important;
        font-size: 1rem !important;
    }
    
    .stSidebar {
        width: 280px !important;
    }
    
    .stChatInput {
        margin: 1rem -1rem 0 -1rem !important;
        padding: 1rem !important;
        border-radius: 0 !important;
    }
}

@media (max-width: 480px) {
    .main-content-adjusted {
        padding-left: 50px !important;
    }
    
    .sidebar-toggle-fixed {
        padding: 0.5rem !important;
        min-width: 36px !important;
        min-height: 36px !important;
    }
    
    .message {
        padding: 1rem !important;
        gap: 0.75rem !important;
        margin: 1rem 0 !important;
    }
    
    .message-icon {
        width: 2rem !important;
        height: 2rem !important;
    }
    
    h1 {
        font-size: 1.75rem !important;
        line-height: 1.2 !important;
    }
    
    .message-content {
        font-size: 0.85rem !important;
        line-height: 1.6 !important;
    }
    
    .stSidebar {
        width: 260px !important;
    }
    
    .stChatInput input {
        font-size: 0.875rem !important;
        padding: 0.875rem 1rem !important;
    }
}

/* Enhanced scrollbar styling with theme support */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: var(--bg-secondary);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: var(--border-color);
    border-radius: 4px;
    transition: background 0.2s ease;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--border-hover);
}

::-webkit-scrollbar-corner {
    background: var(--bg-secondary);
}

/* Firefox scrollbar */
* {
    scrollbar-width: thin;
    scrollbar-color: var(--border-color) var(--bg-secondary);
}

/* Smooth scrolling */
html {
    scroll-behavior: smooth;
}

/* Chat container improvements */
.chat-container {
    max-height: calc(100vh - 200px);
    overflow-y: auto;
    padding-right: 0.5rem;
    margin-right: -0.5rem;
}

/* Footer styling */
hr {
    border: none;
    height: 1px;
    background: var(--border-color);
    margin: 2rem 0 1rem 0;
}

/* Additional animations and micro-interactions */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes slideIn {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}

.message {
    animation: fadeIn 0.3s ease-out;
}

.chat-item {
    animation: slideIn 0.2s ease-out;
}

/* Improved focus states */
button:focus-visible,
input:focus-visible {
    outline: 2px solid var(--accent-primary);
    outline-offset: 2px;
}

/* Better selection colors */
::selection {
    background: rgba(59, 130, 246, 0.2);
    color: var(--text-primary);
}

/* Loading state improvements */
.stSpinner > div {
    border-color: var(--accent-primary) !important;
}

/* Improved toast/notification styling */
.stAlert {
    border-radius: 8px !important;
    border: 1px solid var(--border-color) !important;
    background: var(--bg-secondary) !important;
}

/* Enhanced markdown content styling */
.stMarkdown {
    color: var(--text-secondary) !important;
}

.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, 
.stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
    color: var(--text-primary) !important;
}

.stMarkdown code {
    background: var(--bg-tertiary) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 4px !important;
    padding: 0.2rem 0.4rem !important;
}

.stMarkdown pre {
    background: var(--bg-tertiary) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 8px !important;
}

/* Streamlit specific dark mode overrides */
.stApp[data-theme="dark"] {
    background-color: var(--bg-primary) !important;
}

.stApp[data-theme="dark"] .main .block-container {
    background-color: var(--bg-primary) !important;
}

/* Better mobile experience */
@media (max-width: 480px) {
    .main-content-adjusted {
        padding-left: 50px !important;
    }
    
    .sidebar-toggle-fixed {
        padding: 0.5rem !important;
        min-width: 36px !important;
        min-height: 36px !important;
    }
    
    .message {
        padding: 1rem !important;
        gap: 0.75rem !important;
    }
    
    .message-icon {
        width: 2rem !important;
        height: 2rem !important;
    }
    
    h1 {
        font-size: 1.75rem !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Streamlit Config ---
st.set_page_config(
    page_title="HireScope Chat", 
    layout="wide",
    initial_sidebar_state="expanded" if st.session_state.sidebar_open else "collapsed"
)

# --- Theme Detection Script ---
theme_script = """
<script>
// Theme detection and CSS variable updates
function updateTheme() {
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const streamlitIsDark = window.parent.document.querySelector('[data-theme="dark"]') !== null;
    
    if (isDark || streamlitIsDark) {
        document.documentElement.setAttribute('data-theme', 'dark');
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
    }
}

// Update theme on load
updateTheme();

// Listen for theme changes
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', updateTheme);

// Also check for Streamlit theme changes
const observer = new MutationObserver(updateTheme);
observer.observe(window.parent.document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme']
});
</script>
"""

st.markdown(theme_script, unsafe_allow_html=True)

# --- Helper Functions ---
def generate_chat_title(content):
    """Generate a short title from the first message"""
    words = content.split()[:4]
    return " ".join(words) + ("..." if len(content.split()) > 4 else "")

def create_icon_button(icon_key, button_key, tooltip=""):
    """Create an icon button with proper styling"""
    return f"""
    <button class="icon-button" onclick="document.getElementById('{button_key}').click()" title="{tooltip}">
        {ICONS[icon_key]}
    </button>
    """

# --- Session State Init ---
if "chats" not in st.session_state:
    st.session_state.chats = {}
    initial_title = "New Chat"
    st.session_state.chats[initial_title] = [{"role": "system", "content": "You are a recruiter assistant."}]
    st.session_state.active = initial_title

if "editing_chat" not in st.session_state:
    st.session_state.editing_chat = None

if "dropdown_open" not in st.session_state:
    st.session_state.dropdown_open = {}

if "is_generating" not in st.session_state:
    st.session_state.is_generating = False

# --- Sidebar Toggle Button in Main Content (when sidebar is closed) ---
if not st.session_state.sidebar_open:
    # Create a container at the top for the toggle button
    toggle_container = st.container()
    with toggle_container:
        col1, col2 = st.columns([0.1, 0.9])
        with col1:
            if st.button("☰", key="open_sidebar_btn", help="Open Sidebar", type="primary"):
                st.session_state.sidebar_open = True
                st.rerun()
    
    # Add CSS to make the main content area have proper spacing
    st.markdown('<div class="main-content-adjusted">', unsafe_allow_html=True)

# --- Sidebar ---
if st.session_state.sidebar_open:
    with st.sidebar:
        # Header with collapse button
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            st.markdown("### 💼 HireScope")
        with col2:
            if st.button(">>", key="collapse_sidebar", help="Collapse sidebar"):
                st.session_state.sidebar_open = False
                st.rerun()
        
        st.markdown("---")
        
        # New Chat Button
        if st.button("➕ New Chat", key="new_chat", help="Start a new conversation", use_container_width=True):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            title = f"New Chat"
            counter = 1
            while title in st.session_state.chats:
                title = f"New Chat {counter}"
                counter += 1
            
            st.session_state.chats[title] = [{"role": "system", "content": "You are a recruiter assistant."}]
            st.session_state.active = title
            st.session_state.editing_chat = None
            st.rerun()
        
        st.markdown("---")
        
        # Chat History
        if st.session_state.chats:
            st.markdown("**Recent Chats**")
            
            for chat_key in sorted(st.session_state.chats.keys(), reverse=True):
                is_active = chat_key == st.session_state.active
                is_editing = st.session_state.editing_chat == chat_key
                
                if is_editing:
                    # Rename mode
                    col1, col2 = st.columns([0.85, 0.15])
                    with col1:
                        new_name = st.text_input(
                            "", 
                            value=chat_key, 
                            key=f"rename_{chat_key}",
                            label_visibility="collapsed"
                        )
                    with col2:
                        if st.button("✓", key=f"confirm_{chat_key}", help="Confirm rename", type="primary"):
                            if new_name and new_name != chat_key and new_name not in st.session_state.chats:
                                st.session_state.chats[new_name] = st.session_state.chats.pop(chat_key)
                                if st.session_state.active == chat_key:
                                    st.session_state.active = new_name
                            st.session_state.editing_chat = None
                            st.rerun()
                        
                        # Add cancel button
                        if st.button("⏹", key=f"cancel_{chat_key}", help="Cancel rename"):
                            st.session_state.editing_chat = None
                            st.rerun()
                else:
                    # Normal mode
                    col1, col2 = st.columns([0.85, 0.15])
                    
                    with col1:
                        # Chat selection button
                        button_type = "primary" if is_active else "secondary"
                        if st.button(
                            chat_key, 
                            key=f"select_{chat_key}",
                            help=f"Switch to {chat_key}",
                            use_container_width=True,
                            type=button_type
                        ):
                            st.session_state.active = chat_key
                            st.session_state.editing_chat = None
                            st.rerun()
                    
                    with col2:
                        # Three dots menu
                        if st.button("⋮", key=f"menu_{chat_key}", help="Chat options"):
                            st.session_state.dropdown_open[chat_key] = not st.session_state.dropdown_open.get(chat_key, False)
                            st.rerun()
                    
                    # Dropdown menu with improved styling
                    if st.session_state.dropdown_open.get(chat_key, False):
                        st.markdown("""
                        <div style="
                            background: var(--bg-tertiary);
                            border: 1px solid var(--border-color);
                            border-radius: 8px;
                            padding: 0.5rem;
                            margin: 0.25rem 0;
                            box-shadow: var(--shadow-md);
                        ">
                        """, unsafe_allow_html=True)
                        
                        subcol1, subcol2 = st.columns(2)
                        with subcol1:
                            if st.button("✏️ Rename", key=f"edit_{chat_key}", help="Rename chat", use_container_width=True):
                                st.session_state.editing_chat = chat_key
                                st.session_state.dropdown_open[chat_key] = False
                                st.rerun()
                        with subcol2:
                            if st.button("🗑️ Delete", key=f"delete_{chat_key}", help="Delete chat", use_container_width=True):
                                if len(st.session_state.chats) > 1:
                                    del st.session_state.chats[chat_key]
                                    if st.session_state.active == chat_key:
                                        st.session_state.active = next(iter(st.session_state.chats))
                                    st.session_state.dropdown_open.pop(chat_key, None)
                                    if st.session_state.editing_chat == chat_key:
                                        st.session_state.editing_chat = None
                                    st.rerun()
                        
                        st.markdown('</div>', unsafe_allow_html=True)

# --- Main Chat Area ---
# Enhanced title with gradient and better typography
st.markdown("""
<div style="
    margin: 1rem 0 2rem 0;
    padding: 0;
">
    <h1 style="
        background: var(--gradient-primary);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: -0.05em;
        margin: 0;
        padding: 0;
        text-align: left;
        line-height: 1.1;
    ">💼 HireScope Chat</h1>
    <p style="
        color: var(--text-tertiary);
        font-size: 1.1rem;
        font-weight: 400;
        margin: 0.5rem 0 0 0;
        letter-spacing: 0.01em;
    ">AI-Powered Recruitment Assistant</p>
</div>
""", unsafe_allow_html=True)

# Get active chat
active_key = st.session_state.active
if active_key not in st.session_state.chats:
    # Fallback if active chat was deleted
    active_key = next(iter(st.session_state.chats))
    st.session_state.active = active_key

chat = st.session_state.chats[active_key]

# Display chat messages with improved container
chat_container = st.container()
with chat_container:
    # Add a wrapper div for better styling
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    for msg in chat[1:]:  # Skip system message
        role = msg['role']
        content = msg['content']
        
        if role == "user":
            st.markdown(f"""
            <div class="message user">
                <div class="message-icon">
                    {ICONS['person']}
                </div>
                <div class="message-content">
                    <strong>You</strong>
                    {content}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="message assistant">
                <div class="message-icon">
                    {ICONS['robot']}
                </div>
                <div class="message-content">
                    <strong>HireScope Assistant</strong>
                    {content}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Show skeleton loading animation when generating response
    if st.session_state.is_generating:
        st.markdown(f"""
        <div class="skeleton-container">
            <div class="skeleton-icon">
                {ICONS['robot']}
            </div>
            <div class="skeleton-content">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <strong>HireScope Assistant</strong>
                    <div class="thinking-dots">
                        <div class="thinking-dot"></div>
                        <div class="thinking-dot"></div>
                        <div class="thinking-dot"></div>
                    </div>
                </div>
                <div class="skeleton skeleton-line"></div>
                <div class="skeleton skeleton-line"></div>
                <div class="skeleton skeleton-line"></div>
                <div class="skeleton skeleton-line"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Chat input with improved error handling
prompt = st.chat_input("Ask about candidates, resumes, or hiring...")

if prompt and not st.session_state.is_generating:
    # Add user message
    chat.append({"role": "user", "content": prompt})
    
    # Set generating state to show skeleton
    st.session_state.is_generating = True
    st.rerun()

# Process response if we're in generating state
if st.session_state.is_generating:
    # Add a placeholder for the response
    with st.spinner("Thinking..."):
        # Generate response
        try:
            total = collection.count()
            if total == 0:
                reply = "⚠️ No resume data available. Please upload some resumes to get started."
            else:
                # Query the vector database
                hits = collection.query(query_texts=[chat[-1]["content"]], n_results=3)
                context = "\n---\n".join(hits.get("documents", [[]])[0])
                
                # Update system message with context
                chat[0]["content"] = f"""You are a recruiter assistant. Answer ONLY from these résumé snippets:
{context}
Be helpful, professional, and provide specific information from the resumes when available."""
                
                # Get AI response
                result = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=chat,
                    temperature=0.3,
                    max_tokens=1000
                )
                reply = result.choices[0].message.content
                
        except Exception as e:
            reply = f"⚠️ Error processing your request: {str(e)}"
            st.error(f"An error occurred: {str(e)}")
        
        # Add assistant response
        chat.append({"role": "assistant", "content": reply})
        
        # Update chat title if it's still default
        if active_key.startswith("New Chat") and len(chat) == 3:  # System + User + Assistant
            new_title = generate_chat_title(chat[-2]["content"])  # Use user message for title
            if new_title != active_key:
                st.session_state.chats[new_title] = st.session_state.chats.pop(active_key)
                st.session_state.active = new_title
        
        # Reset generating state
        st.session_state.is_generating = False
        st.rerun()

# Close the main content div if sidebar is closed
if not st.session_state.sidebar_open:
    st.markdown('</div>', unsafe_allow_html=True)

# Footer with better styling
st.markdown("---")
st.markdown("""
<div style="
    text-align: center; 
    color: var(--text-tertiary); 
    font-size: 0.875rem;
    font-weight: 400;
    padding: 1rem 0;
    margin-top: 2rem;
    letter-spacing: 0.02em;
">
    <strong style="color: var(--text-secondary); font-weight: 600;">HireScope Chat</strong> 
    <span style="margin: 0 0.5rem;">•</span>
    AI-Powered Recruitment Assistant
    <span style="margin: 0 0.5rem;">•</span>
    Built with ❤️ using Streamlit
</div>
""", unsafe_allow_html=True)