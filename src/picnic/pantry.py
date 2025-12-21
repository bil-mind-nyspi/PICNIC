#!/usr/bin/env python3

# =======================================
# Imports
import os
import FreeSimpleGUI as sg
import base64
import tempfile
import importlib
from io import BytesIO

from PIL import (
    Image,
    ImageDraw,
    ImageFont
)

from picnic.cards import get_path_to_jsons
from picnic.input_deck_reader import (
    read_input_deck,
    make_card
)


# =======================================
# Constants
COLORTHEMES = [
    'DarkBlue14',
    'Default',
    'DarkPurple1'
]
LEFTROUND = [
    b'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',
    b'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',
    b'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',
    b'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'
]
RIGHTROUND = [
    b'iVBORw0KGgoAAAANSUhEUgAAABsAAABzCAYAAABpc3liAAABhGlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw0AYht+mSkUrDlYQcchQneyiIo6lFYtgobQVWnUwufQPmjQkKS6OgmvBwZ/FqoOLs64OroIg+APi7OCk6CIlfpcUWsR4x3EP733vy913gNCsMtXsiQKqZhnpREzM5VfFwCsEmiMIYEBipp7MLGbhOb7u4eP7XYRnedf9OQaVgskAn0gcZbphEW8Qz21aOud94hArSwrxOfGUQRckfuS67PIb55LDAs8MGdl0nDhELJa6WO5iVjZU4lnisKJqlC/kXFY4b3FWq3XWvid/YbCgrWS4TmscCSwhiRREyKijgiosRGjXSDGRpvOYh3/M8afIJZOrAkaOBdSgQnL84H/wu7dmcWbaTQrGgN4X2/6YAAK7QKth29/Htt06AfzPwJXW8deawPwn6Y2OFj4ChraBi+uOJu8BlzvA6JMuGZIj+WkJxSLwfkbflAeGb4H+Nbdv7XOcPgBZ6tXyDXBwCEyWKHvd49193X37t6bdvx8pOXKJ1ElYXQAAAAZiS0dEALUAugDZFqItrQAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB+gCDRQUGnaKnXEAAAPJSURBVGje7dtfSFtXHMDxb3LvqmlMrSLq5nQto5M5RgvrWmgrw7G97GHQPe15UArbHjbGSlfYcOyhYzBwjD1sQjf6MPZUKZ0ORmnrnEKtlFU0NUnVNOo0UeKfemP+3Zs9xBMuos6Ye3w6BwLnd3IuH87f3IdfXNd7RnLJ5BrG6gqLiwu52dmplH/kfqzn919DgB8YAvqASUosru4/A7nNvliYn2N8/CF3bnXz150bAP1AF/AbMLMr7P1PO3Mulwtd1/CU7cO734PP56XSV0HlAR+a5iYUHKH3dg83rl8FeAJcAX4EHhaNbdehrqaK+roaDlb6CI494OrPHYSCwwBxoAP4FkjsBNNePf12+3YdjESS6Hycf+fmqa9v4Ezrm9TWPsM/9/s9QBtwcn1a/3dN3TudgkwmS2A8QjA8x9FX2rhwqUN89QbwC3DOMUyUVCpDcGKaiqpGLrX/JJobge+AC45ioszF4mRyHi5+UQA9wJfbge5Szo2RSJJI63x88QfRVA60bzWl7lIPatY0yebKOffh1/YRfg687jgGYFoWZd4a3jr7gX0NPwP2O44BWFaO5184xonWd+y79BMpWH6E8PKxM1TVNImmj4AXpWAAZeU+Tr1WGF01cF4aBtD4XDMtR9tE+B7QIA1zazrNLSdE6APelYYB1D59iMNHjovwrFRM03SaXzopwtPAYWkYQG1dkz1slYpVHKjmSMspER6XigE829Qsqi3SsYPVdaJ6SDrm9VYWllA6VlZeuIu90jH9qX2Fsy4d0zRNzq2/xdviXmIoTGEKU5jCFKYwhSlMYQpTmMIUpjCFKUxhClOYwhSmMIUpTGFFl9zeYaZp7h2WzaRF1ZKOpZKF/C9DOmYYy6Iak44txaOiGpaOTUcCouqXiq2uxAn5B0Q4JBWLRSP2sM8t73xlCYzeFWE/MCkNi82GmQwNibBL2qHOZjME/IMifEI+tVQONhMJ4n9wW4RXWM9hdRxbXlpgoPeaCOPkc1edvxvT6SShsXssLhR2YQe2JFkHE/NMwo+GGewrjOom+eRYZ299y7J4PDHKze5O0TQFXGZDFq7uxIgeT4zyR9f3omkN+Aq4tbGvXuoahR8N20eUJJ8m2rlZf72UXRcau2dfo7V16JutntF3c2BnIkEGeq/Zd93U+tR1bvesXsxdF5sNE/AP2g+s2HWXN1ujorHVlTixaITA6F37XScObFG537p43TJNk2wmTSqZwDCWWYpHmY4E7L9H9rtuV1nt4sVuJ5+/yWfPNux2U22cRgswgBgQxuF/IvwH+vtfOu7qz6YAAAAASUVORK5CYII=',
    b'iVBORw0KGgoAAAANSUhEUgAAABsAAABzCAYAAABpc3liAAABhGlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw0AYht+mSkUrDlYQcchQneyiIo6lFYtgobQVWnUwufQPmjQkKS6OgmvBwZ/FqoOLs64OroIg+APi7OCk6CIlfpcUWsR4x3EP733vy913gNCsMtXsiQKqZhnpREzM5VfFwCsEmiMIYEBipp7MLGbhOb7u4eP7XYRnedf9OQaVgskAn0gcZbphEW8Qz21aOud94hArSwrxOfGUQRckfuS67PIb55LDAs8MGdl0nDhELJa6WO5iVjZU4lnisKJqlC/kXFY4b3FWq3XWvid/YbCgrWS4TmscCSwhiRREyKijgiosRGjXSDGRpvOYh3/M8afIJZOrAkaOBdSgQnL84H/wu7dmcWbaTQrGgN4X2/6YAAK7QKth29/Htt06AfzPwJXW8deawPwn6Y2OFj4ChraBi+uOJu8BlzvA6JMuGZIj+WkJxSLwfkbflAeGb4H+Nbdv7XOcPgBZ6tXyDXBwCEyWKHvd49193X37t6bdvx8pOXKJ1ElYXQAAAAZiS0dEALUAugDZFqItrQAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB+gCDRQzLGP1uo0AAAOaSURBVGje7dtNaBxlHMfx78zOrkmat52QVI1KGmxDbSsUm0MtUZAeBE/ePCvSo4InD0JFQRCKxZsUiuClt4AVRC0ekqaCjW8VN2WzJS9N0maTbvb9dWaeHnafcZA0r/N46TOw8Pyf3dnP7szzf/byW+PjL8ZFvValWilRyG+IzPr92vydRHr6xvezQAKYBiaBOfZ5GJ9+eVVs9kRuY52VpTv8OT3BP39MAEwB48AVYHlPWNvhcyJmGsQPROmPt9EX78S2u7DtbuJ2L9FohKWFWf76bYJfJ78DKACXga+AmV1jW73g5WMHGT70FP0DvSwvJvnx22+4v5wCyAAXgQtAORRMHge7YpwZHaanJ0Zq5iY/Xf1aPnUN+Az4ebv3iFh9p87vBCvVXWbm1nmwmuPIyAgjR18kcesGwDDwGlAEfg8Fk0e+6jAz94AnbZsTJ09z++/rAD3AWaDRWkjhYPJYWC1iiggnR8dIJaYAosDYVqC5n75J3ityK1ni1Tfek1NtwHng3dAxgEzF4fZig5deeUdOtQMfte5juBhAruqylInRN/S6nHoW+BDoCB0DyNU8uu1hzJ5ROXUW+EAJBnCv4PL0c8fB7JVT7wNHlWAA69UY1sBpWdrAOWUYQHv3Mxgd/hd6GxhUhjWEidV7WJZdwFvKMIBIxwBGbEiWbyrFMCJE4kdkdQY4pA4DzPb+YDmmFot2YrQ9L8tTSjEAs3NQDl9Qj8X8Bh9SjhlRf3scUI9FnpDDA+ox0/KvqHIMI6Jm1992sWhMYxrTmMY0pjGNaUxjGtOYxjSmMY1pTGMa05jGNKYxjWlMY487Jtz/DxOeI4eeesytyWFJPdbww2Zp5ZhXz8rhvHqs6AcGE0oxr1FEVFOynFaLVdaC5aSpsr/cjaSspoA5ZZhbTiPq87IcV9bUwnNwsrOyLNCMlqrB3NIKouwnSC/TyrCa4fdVHif9iywzNLOr4e+NwqvjZFPg+Y18kUBI1gxRwskv4OVuyplrNMOxIe/6wsMpLOKu+RnYuzRDseVwsRbkrP4gZyrAJ2ySvrX2fY/yC8FvVKUZE7202eutfa26bCp4jyot6PNHnWPtpWHd0kpzef+76u62Lt2lrc61drXXldM42dlgw8pVt6OE9LaY1yjiVdZwN5LBvU427K6y31bwkwvPQbg1RKOMV8/iFZeDv0fBvW5PqXYAscPHdZrp2cG9Lqr/XkYPKAFpYJ6Q/4nwELMaY2S6GtFsAAAAAElFTkSuQmCC',
    b'iVBORw0KGgoAAAANSUhEUgAAABsAAABzCAYAAABpc3liAAABhGlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw0AYht+mSkUrDlYQcchQneyiIo6lFYtgobQVWnUwufQPmjQkKS6OgmvBwZ/FqoOLs64OroIg+APi7OCk6CIlfpcUWsR4x3EP733vy913gNCsMtXsiQKqZhnpREzM5VfFwCsEmiMIYEBipp7MLGbhOb7u4eP7XYRnedf9OQaVgskAn0gcZbphEW8Qz21aOud94hArSwrxOfGUQRckfuS67PIb55LDAs8MGdl0nDhELJa6WO5iVjZU4lnisKJqlC/kXFY4b3FWq3XWvid/YbCgrWS4TmscCSwhiRREyKijgiosRGjXSDGRpvOYh3/M8afIJZOrAkaOBdSgQnL84H/wu7dmcWbaTQrGgN4X2/6YAAK7QKth29/Htt06AfzPwJXW8deawPwn6Y2OFj4ChraBi+uOJu8BlzvA6JMuGZIj+WkJxSLwfkbflAeGb4H+Nbdv7XOcPgBZ6tXyDXBwCEyWKHvd49193X37t6bdvx8pOXKJ1ElYXQAAAAZiS0dEALUAugDZFqItrQAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB+gCDRQpMinXfTUAAAO4SURBVGje7dtdaFNnHMfxb9LTJn2xpbYqbZ3YXWxaHI5N8EKFobtQUDYvxG13KwxvNpiIgheKwwthUNaBgiIqgojtkE4UWrA6tY19oYpSyUoVU62mJjWxqU2aY5JzdpE+h7Ot1r6cpxfyPBB4/s8hfHjynOc55+IXl35KNxNvEozERwjFQubj8GPd1+8LH/vr2EPAD/QAbUCAOTaXedY0J7vwLPqMe0/u0dDRwLmucwA+oAm4ADyfFRbYeN/EBW5vDjlFGlpJHrmlXjyl+XhKCzE0kzuBOzR2NlLfWg/wGjgNnAD+njk2RfNWF1GwrASt3IMv0MHBPw7S+aQTIArUA3VAwhFMNHd+DgtWlTFSFOdibxN7G/eKS63AEeC6Y5iFFml4a4q5NdLJjuM7xPAgcBg4OeV3Z7rIxliaRHeU9cZn3Nx1TQx/APwO7HMUEy35aIzqlxV01N4UQ/nAL1OB7rnsm8yrFBXBhbR/a83QCxwCfnAcAzDfGCyNLqJl25/2GR4ANjqOAZgpk4/1ao5/+pt9DfcDBY5jAKRhU+UX7F++W4x8CeyRgwFa0s3XH25ltWeVGPoZWCkFA1hMOXs++lGUC4Fd0jCAteWf8/2S70RZC1RJw/JceWyt3CzKBcA30jCAT0pq+Kp0iyi3S8Vy3blsq7SwdUC1NAygpmSFvdwgFavwLmFn+XZRrpGKAawtW2NNVDq2vGCZ1ZWOLfKUWftdOlacWyy6hdKx/ByvdVpJxzS3JufUn/SNCtf8YdKeZwpTmMIUpjCFKUxhClOYwhSmMIUpTGEKU5jCFKYwhSlMYQp7jzETc/6wtJGeP2w8kxRdQzo2mhoV3bh0bFiPiG5YOjaQeGp1pWNdkR7R9UvFhpIhGl42ibJHKuaP9dnLNmlYykhxOdgsSh8QkIb1xvxcemVhTdI2tW7oXAm2iPI12WipHKw7cpczofOiPM1EhtVxbDDxnLr+o6KMks2uOn82jqXjNL+4yn39gRiqxxaSdQxLmxluhNs5MmAlAVvJhmOdPfUzZoa24dv81GeFNgfJhmL/lcLVnJhR2/Btah9YYbxxsmHY/6Vvtbmu0Y1wu31GSbIx0UlTt9pc7rrmF1ftazQ+Af36tu9os9mw3ZG71PUftd9108oRazM563pjfq4EW+wbVtx100pIvxMbSobwx/q4HGy2n3Viw84o+62J1620kWY8k2Q0NcqwHmEg8ZSuSI/9eWQ/62aVas9a0/u0k03PVs32pvrvz2gAcSAMDODwPxH+AVNyVs+P+/L2AAAAAElFTkSuQmCC',
    b'iVBORw0KGgoAAAANSUhEUgAAABsAAABzCAYAAABpc3liAAABhGlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw0AYht+mSkUrDlYQcchQneyiIo6lFYtgobQVWnUwufQPmjQkKS6OgmvBwZ/FqoOLs64OroIg+APi7OCk6CIlfpcUWsR4x3EP733vy913gNCsMtXsiQKqZhnpREzM5VfFwCsEmiMIYEBipp7MLGbhOb7u4eP7XYRnedf9OQaVgskAn0gcZbphEW8Qz21aOud94hArSwrxOfGUQRckfuS67PIb55LDAs8MGdl0nDhELJa6WO5iVjZU4lnisKJqlC/kXFY4b3FWq3XWvid/YbCgrWS4TmscCSwhiRREyKijgiosRGjXSDGRpvOYh3/M8afIJZOrAkaOBdSgQnL84H/wu7dmcWbaTQrGgN4X2/6YAAK7QKth29/Htt06AfzPwJXW8deawPwn6Y2OFj4ChraBi+uOJu8BlzvA6JMuGZIj+WkJxSLwfkbflAeGb4H+Nbdv7XOcPgBZ6tXyDXBwCEyWKHvd49193X37t6bdvx8pOXKJ1ElYXQAAAAZiS0dEALUAugDZFqItrQAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB+gCDRQdC834BsoAAAMeSURBVGje7Zu9a9tAGIcfK3LirxhTSOIcgRRv7dyx3bqXbh27dezQP6CFDoVCIKspeM6WfyB0Cdkyp0NJHHCCiRMbHMmSFX24g3Ph6rrNh3VT753uPQk/fr9OAv+caTQao1wuR6lUYnFxcVQul4NKpdLJ5/M/gQNgH9gVQjSZ0TL1en007cLy8jKrq6usrKywsLAAsAdsA1tCiNMHwUZjI45jgiDA8zz6/T4XFxecnJzgOA61Wo21tTUKhQKAAzSAuhDix71h/7qh2+3SarU4OjqiWq2yvr6OZVkAPWAT2BBCeKnApEVRRLPZpN1us7S0RKVSkZd2gC9CiO+pwaSFYcjh4SG+71OtVuV2C/gshPiWKkza+fk5vV6Pcrkst3zgkxDia+owAN/36XQ6zM/Py60h8PFvwJlgAHEcc3Z2RiaTUSN8Py2lM8MAkiSh2+0SRZFaw7eTTZMKTAIvLy/xfV/t0lfqWFikZJZlUSgU5GkD8BL4oCUytWn6/T7XH9sDnsuTxiJly+fzlEol6T4C3mmLbErDOMATIcRp6pHJ+hWLRekuAm+0pFFN59zcnHRfa0ujNMdxcF1XujVtkQHkcjnVfaEVls1m1VQ+0woD1CF/qh2WzWbl8rF2mG3bN+9Q2mFKzYraYdcvR+OlbpjyUEU77LcoDczADMzADMzADMzADMzADMzADMzADMzADMzADMzADMzADMzADMzA/nOY+pu7dliSJDdL7bA4juVyoB2m6Ho62mFhGMrlsXZYEARyeWDpjkqp2b5W2HA4VN1dS+d8KRqsPSFEUxvM9301hdvahjpJEgaDgXQdYEsbzPM8db4aUsOaOuzq6koVCfWAupazMY5jXNdVD99NVSRrpdl9ruuqQ7wDbKT+iJEgz7tRF7YYi2K9VGESpNTJZyyG/UN9a6dRIyWiIWMR7FTVrT1r1yk1ulVtaz9kYD3Pm+y6O+mI7fuedYPBQB1Y2XV3UkjfCgvDkOFwOHnWyYG9l/bbVr95kiTEcUwURYRhSBAEkwB51j1I1W632+273juzXn8yjQkwADrAMSn/E+EX5ymk8oGWp4QAAAAASUVORK5CYII='
]
MIDDLE = [
    b'iVBORw0KGgoAAAANSUhEUgAAAtUAAABzCAYAAABXaf6xAAABhGlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw0AYht+mSkUrDlYQcchQneyiIo6lFYtgobQVWnUwufQPmjQkKS6OgmvBwZ/FqoOLs64OroIg+APi7OCk6CIlfpcUWsR4x3EP733vy913gNCsMtXsiQKqZhnpREzM5VfFwCsEmiMIYEBipp7MLGbhOb7u4eP7XYRnedf9OQaVgskAn0gcZbphEW8Qz21aOud94hArSwrxOfGUQRckfuS67PIb55LDAs8MGdl0nDhELJa6WO5iVjZU4lnisKJqlC/kXFY4b3FWq3XWvid/YbCgrWS4TmscCSwhiRREyKijgiosRGjXSDGRpvOYh3/M8afIJZOrAkaOBdSgQnL84H/wu7dmcWbaTQrGgN4X2/6YAAK7QKth29/Htt06AfzPwJXW8deawPwn6Y2OFj4ChraBi+uOJu8BlzvA6JMuGZIj+WkJxSLwfkbflAeGb4H+Nbdv7XOcPgBZ6tXyDXBwCEyWKHvd49193X37t6bdvx8pOXKJ1ElYXQAAAAZiS0dEALUAugDZFqItrQAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB+gCDRQWGzO7z2UAAAIWSURBVHja7dixEYBADANBmaH/bj6BjC6oxvTgz5jdEhTdqNb1dgAAgJHuzmEGAACYq6qc634sAQAAGzzVAAAgqgEAQFQDAICoBgAAUQ0AAIhqAAAQ1QAAIKoBAEBUAwAAohoAAEQ1AACIagAAENUAAICoBgAAUQ0AAKIaAABENQAAIKoBAEBUAwCAqAYAAFENAACIagAAENUAACCqAQBAVAMAAKIaAABENQAAiGoAABDVAACAqAYAAFENAACiGgAARDUAACCqAQBAVAMAgKgGAABRDQAAiGoAABDVAAAgqgEAQFQDAACiGgAARDUAAIhqAAAQ1QAAIKoBAABRDQAAohoAAEQ1AACIagAAQFQDAICoBgAAUQ0AAKIaAAAQ1QAAIKoBAEBUAwCAqAYAAEQ1AACIagAAENUAACCqAQAAUQ0AAKIaAABENQAAiGoAAEBUAwCAqAYAAFENAACiGgAAENUAACCqAQBAVAMAgKgGAABENQAAiGoAABDVAAAgqgEAAFENAACiGgAARDUAAIhqAABAVAMAgKgGAABRDQAAohoAABDVAAAgqgEAQFQDAICoBgAAUQ0AAIhqAAAQ1QAAIKoBAEBUAwAAohoAAEQ1AACIagAAENUAAICoBgAAUQ0AAKIaAABENQAAIKoBAEBUAwCAqAYAAFENAACIagAAENUAACCqAQDg3ypJmwEAAOY81QAAsOkDKJoKX1a5sggAAAAASUVORK5CYII=',
    b'iVBORw0KGgoAAAANSUhEUgAAAtUAAABzCAYAAABXaf6xAAABhGlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw0AYht+mSkUrDlYQcchQneyiIo6lFYtgobQVWnUwufQPmjQkKS6OgmvBwZ/FqoOLs64OroIg+APi7OCk6CIlfpcUWsR4x3EP733vy913gNCsMtXsiQKqZhnpREzM5VfFwCsEmiMIYEBipp7MLGbhOb7u4eP7XYRnedf9OQaVgskAn0gcZbphEW8Qz21aOud94hArSwrxOfGUQRckfuS67PIb55LDAs8MGdl0nDhELJa6WO5iVjZU4lnisKJqlC/kXFY4b3FWq3XWvid/YbCgrWS4TmscCSwhiRREyKijgiosRGjXSDGRpvOYh3/M8afIJZOrAkaOBdSgQnL84H/wu7dmcWbaTQrGgN4X2/6YAAK7QKth29/Htt06AfzPwJXW8deawPwn6Y2OFj4ChraBi+uOJu8BlzvA6JMuGZIj+WkJxSLwfkbflAeGb4H+Nbdv7XOcPgBZ6tXyDXBwCEyWKHvd49193X37t6bdvx8pOXKJ1ElYXQAAAAZiS0dEALUAugDZFqItrQAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB+gCDRQ1Aul5EMQAAAIWSURBVHja7dhBEYBAEAPBLC+MoA0jKDgrCFw83P6obgl5TaWe9XYAAIA93TmsAAAAA1Wp87o91QAAMOCpBgAAUQ0AAKIaAABENQAAiGoAAEBUAwCAqAYAAFENAACiGgAAENUAACCqAQBAVAMAgKgGAABENQAAiGoAABDVAAAgqgEAAFENAACiGgAARDUAAIhqAABAVAMAgKgGAABRDQAAohoAABDVAAAgqgEAQFQDAICoBgAARDUAAIhqAAAQ1QAAIKoBAABRDQAAohoAAEQ1AACIagAAQFQDAICoBgAAUQ0AAKIaAAAQ1QAAIKoBAEBUAwCAqAYAAFENAACIagAAENUAACCqAQBAVAMAAKIaAABENQAAiGoAABDVAACAqAYAAFENAACiGgAARDUAACCqAQBAVAMAgKgGAABRDQAAiGoAABDVAAAgqgEAQFQDAACiGgAARDUAAIhqAAAQ1QAAgKgGAABRDQAAohoAAEQ1AAAgqgEAQFQDAICoBgAAUQ0AAIhqAAAQ1QAAIKoBAEBUAwAAohoAAEQ1AACIagAAENUAAICoBgAAUQ0AAKIaAABENQAAiGoAAEBUAwCAqAYAAFENAACiGgAAENUAACCqAQBAVAMAgKgGAABENQAAiGoAABDVAAAgqgEAAFENAACiGgAARDUAAIhqAABAVAMAgKgGAABRDQAA/1ZJ2gwAALDPUw0AAEMf4DMIPs5obHYAAAAASUVORK5CYII=',
    b'iVBORw0KGgoAAAANSUhEUgAAAtUAAABzCAYAAABXaf6xAAABhGlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw0AYht+mSkUrDlYQcchQneyiIo6lFYtgobQVWnUwufQPmjQkKS6OgmvBwZ/FqoOLs64OroIg+APi7OCk6CIlfpcUWsR4x3EP733vy913gNCsMtXsiQKqZhnpREzM5VfFwCsEmiMIYEBipp7MLGbhOb7u4eP7XYRnedf9OQaVgskAn0gcZbphEW8Qz21aOud94hArSwrxOfGUQRckfuS67PIb55LDAs8MGdl0nDhELJa6WO5iVjZU4lnisKJqlC/kXFY4b3FWq3XWvid/YbCgrWS4TmscCSwhiRREyKijgiosRGjXSDGRpvOYh3/M8afIJZOrAkaOBdSgQnL84H/wu7dmcWbaTQrGgN4X2/6YAAK7QKth29/Htt06AfzPwJXW8deawPwn6Y2OFj4ChraBi+uOJu8BlzvA6JMuGZIj+WkJxSLwfkbflAeGb4H+Nbdv7XOcPgBZ6tXyDXBwCEyWKHvd49193X37t6bdvx8pOXKJ1ElYXQAAAAZiS0dEALUAugDZFqItrQAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB+gCDRQrC0Tkl78AAAITSURBVHja7dhBEYAwFEPBH6ThFEkoQErqob0xuxJyepP0aQcAANjSdi4zAADAviST73491QAAcMBTDQAAohoAAEQ1AACIagAAENUAAICoBgAAUQ0AAKIaAABENQAAIKoBAEBUAwCAqAYAAFENAACIagAAENUAACCqAQBAVAMAAKIaAABENQAAiGoAABDVAACAqAYAAFENAACiGgAARDUAACCqAQBAVAMAgKgGAABRDQAAiGoAABDVAAAgqgEAQFQDAACiGgAARDUAAIhqAAAQ1QAAgKgGAABRDQAAohoAAEQ1AAAgqgEAQFQDAICoBgAAUQ0AAKIaAAAQ1QAAIKoBAEBUAwCAqAYAAEQ1AACIagAAENUAACCqAQAAUQ0AAKIaAABENQAAiGoAAEBUAwCAqAYAAFENAACiGgAAENUAACCqAQBAVAMAgKgGAABENQAAiGoAABDVAAAgqgEAAFENAACiGgAARDUAAIhqAABAVAMAgKgGAABRDQAAohoAABDVAAAgqgEAQFQDAICoBgAARDUAAIhqAAAQ1QAAIKoBAABRDQAAohoAAEQ1AACIagAAENUAAICoBgAAUQ0AAKIaAABENQAAIKoBAEBUAwCAqAYAAFENAACIagAAENUAACCqAQBAVAMAAKIaAABENQAAiGoAABDVAACAqAYAAFENAACiGgAA/i0zUzMAAMA+TzUAABxauF0Lco+fZ/kAAAAASUVORK5CYII=',
    b'iVBORw0KGgoAAAANSUhEUgAAAtUAAABzCAYAAABXaf6xAAABhGlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw0AYht+mSkUrDlYQcchQneyiIo6lFYtgobQVWnUwufQPmjQkKS6OgmvBwZ/FqoOLs64OroIg+APi7OCk6CIlfpcUWsR4x3EP733vy913gNCsMtXsiQKqZhnpREzM5VfFwCsEmiMIYEBipp7MLGbhOb7u4eP7XYRnedf9OQaVgskAn0gcZbphEW8Qz21aOud94hArSwrxOfGUQRckfuS67PIb55LDAs8MGdl0nDhELJa6WO5iVjZU4lnisKJqlC/kXFY4b3FWq3XWvid/YbCgrWS4TmscCSwhiRREyKijgiosRGjXSDGRpvOYh3/M8afIJZOrAkaOBdSgQnL84H/wu7dmcWbaTQrGgN4X2/6YAAK7QKth29/Htt06AfzPwJXW8deawPwn6Y2OFj4ChraBi+uOJu8BlzvA6JMuGZIj+WkJxSLwfkbflAeGb4H+Nbdv7XOcPgBZ6tXyDXBwCEyWKHvd49193X37t6bdvx8pOXKJ1ElYXQAAAAZiS0dEALUAugDZFqItrQAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB+gCDRQeDHixwKoAAAISSURBVHja7dixDcBADAOxd5D9e0/oMZQd3l1AjqDqoOruHAAA4EpVnccMAABwL8mpJJ5qAABY8FQDAICoBgAAUQ0AAKIaAABENQAAIKoBAEBUAwCAqAYAAFENAACIagAAENUAACCqAQBAVAMAAKIaAABENQAAiGoAABDVAACAqAYAAFENAACiGgAARDUAACCqAQBAVAMAgKgGAABRDQAAiGoAABDVAAAgqgEAQFQDAACiGgAARDUAAIhqAAAQ1QAAgKgGAABRDQAAohoAAEQ1AAAgqgEAQFQDAICoBgAAUQ0AAIhqAAAQ1QAAIKoBAEBUAwCAqAYAAEQ1AACIagAAENUAACCqAQAAUQ0AAKIaAABENQAAiGoAAEBUAwCAqAYAAFENAACiGgAAENUAACCqAQBAVAMAgKgGAABENQAAiGoAABDVAAAgqgEAAFENAACiGgAARDUAAIhqAABAVAMAgKgGAABRDQAAohoAABDVAAAgqgEAQFQDAICoBgAARDUAAIhqAAAQ1QAAIKoBAABRDQAAohoAAEQ1AACIagAAQFQDAICoBgAAUQ0AAKIaAABENQAAIKoBAEBUAwCAqAYAAFENAACIagAAENUAACCqAQBAVAMAAKIaAABENQAAiGoAABDVAACAqAYAAFENAACiGgAARDUAACCqAQBAVAMAgKgGAIB/e2fGCgAAsOCpBgCApQ9tcA1iBRw5awAAAABJRU5ErkJggg=='
]
TEXTCOLOR = [
    (106, 117, 155, 255),
    (  8,  37, 103, 255),
    (223,  66, 209, 255),
    (255, 255, 255, 255),
]
THEME_IDX = 0

PADDING = 4
CARD_SIZE = (780, 116)

FOOTER_BUTTON_SIZE = (17, 2)

# =======================================
# Classes
class Deck():
    def __init__(self):
        """
        :Parameters:
            (none)
        """
        self.cards = []
        self.variables = {}

    def add_card(self, card):
        """
        add a new card to the input deck

        :Parameters:
          -. `card` : input_deck_reader.Card obj, a picnic-like card
        """
        self.cards.append(card)
    
    def can_remove_card(self):
        """
        a boolean on whether a card CAN be removed
        """
        return (len(self.cards) > 0)

    def remove_card(self, idx):
        """
        :Parameters:
          -. `idx` : int, the integer of card to be removed
        """
        if self.can_remove_card:
            del self.cards[idx]
    
    def clear_cards(self):
        """
        delete all the cards
        """
        self.cards = []
    
    def build_graph_element(self, graph, depressed=-1):
        """
        build the canvas for which to draw

        :Parameters:
          -. `graph` : FreeSimpleGUI.Graph element, the graph to be drawn on
          -. `depressed` : int, clicking on a button changes the color
        """
        # clear the graph
        graph.erase()
        
        # create a button (image placed on a graph) for each card
        height = 0
        for idx, card in enumerate(self.cards):
            # check if the user has clicked on this particular card
            #   if they have - "depress" the button
            if idx == depressed:
                theme_idx = -1
                text_color = TEXTCOLOR[THEME_IDX]
            else:
                theme_idx = THEME_IDX
                text_color = TEXTCOLOR[-1]
            
            # draw the left round
            graph.draw_image(
                data = LEFTROUND[theme_idx],
                location = (0, height)
            )
            
            # start preparing the middle "round"
            # open the rounded rectangle image and prepare to draw on it
            tmp_file = tempfile.NamedTemporaryFile(suffix=".png").name
            img = Image.open(BytesIO(base64.b64decode(MIDDLE[theme_idx])))
            draw = ImageDraw.Draw(img)
            
            # create font for the card name/instance name
            try:
                font = ImageFont.truetype('Arial.ttf', size=36)
            except OSError:
                font = ImageFont.truetype('arial.ttf', size=36)

            try:
                card_text = card.cardname + ' - ' + card.parameters['name']
            except KeyError:
                card_text = card.cardname

            draw.text(
                (0, 24),
                text = card_text,
                font = font,
                fill = text_color,
                stroke_width = 1,
                stroke_fill = text_color
            )
            
            # create text for the dataline font
            try:
                font = ImageFont.truetype('Arial.ttf', size=24)
            except OSError:
                font = ImageFont.truetype('arial.ttf', size=24)

            if not card.datalines:
                txt = 'Select file'
            else:
                dl = []
                for d in card.datalines:
                    d = d[0]
                    if d.startswith('@'):
                        dl.append(d)
                    else:
                        dl.append(os.path.basename(d))
                txt = ', '.join(dl)
            draw.text(
                (24, 72),
                text = txt,
                font = font,
                fill = text_color
            )
            
            # save the image in the tempfile
            img.save(tmp_file)
            
            # draw the image on the graph
            graph.draw_image(filename = tmp_file, location=(27, height))
            
            # draw the right round
            graph.draw_image(
                data = RIGHTROUND[theme_idx],
                location = (752, height)
            )
            
            # add to height and change the colors back
            height += CARD_SIZE[1] + PADDING
            w, h = graph.CanvasSize
            graph.CanvasSize = (w, h + CARD_SIZE[1] + PADDING)
            graph.BottomLeft = (0, h + CARD_SIZE[1] + PADDING)
        
        return graph
    
    def check_for_variables(self):
        """
        check if there are any variables in the parameters or datalines
        """
        for card in self.cards:
            # loop over all the datalines to look for variables
            for dataline in card.datalines:
                idx = dataline[0].find('{')
                while idx >= 0:
                    start = idx
                    end = dataline[0].find('}', idx)+1
                    variable_name = dataline[0][idx:end]
                    if not variable_name in self.variables.keys():
                        self.variables[variable_name] = ''
                    
                    idx = dataline[0].find('{', end)
                    
            # loop over all the parameters to check for variables
            for parameter in card.parameters.values():
                idx = parameter.find('{')
                while idx >= 0:
                    start = idx
                    end = parameter.find('}', idx)+1
                    variable_name = parameter[idx:end]
                    if not variable_name in self.variables.keys():
                        self.variables[variable_name] = ''
                    
                    idx = parameter.find('{', end)
                    
            
    def satisy_variables(self):
        """
        check all the cards for variables and create a window to prompt the
        user to satisy those unfilled variables
        """
        self.check_for_variables()
        new_variables = create_variable_window(self.variables)
        if not new_variables is None:
            self.variables = new_variables

# =======================================
# Functions
def create_main_window(deck, theme, window=None):
    """
    create the main window

    :Parameters:
      -. `deck` : input_deck_reader.InputDeck obj, a picnic input deck
      -. `theme` : str, a FreeSimpleGUI default color
      -. `window` : FreeSimpleGUI.Window, if one already exists, overwrite it
    """
    # set the theme, this can be changed from the menubar
    sg.theme(theme)
    
    """
    create a layout that looks like:
    +---------------------------------------------+
    | Settings                                    |
    +---------------------------------------------+
    |                                             |
    |   +-------------------------------------+   |
    |   | Graph that acts as a canvsas      |^|   |
    |   |                                   | |   |
    |   |                                   | |   |
    |   |                                   | |   |
    |   |                                   | |   |
    |   |                                   | |   |
    |   |                                   | |   |
    |   |                                   |*|   |
    |   +-------------------------------------+   |
    |                                             |
    |   [load ] [ add ] [clear] [save ] [ run ]   |
    +---------------------------------------------+
    """
    # this graph element is where all the cards show up
    h = 20 + (len(deck.cards) * (CARD_SIZE[1] + PADDING))
    graph = sg.Graph(
        canvas_size = (800, h),
        graph_bottom_left = (0, h),
        graph_top_right = (800, 0),
        key = '-CANVAS-',
        enable_events = True,
        drag_submits = True
    )
    
    # define the actual layout
    layout = [
        [
            # create a menubar to enable the user to change settings
            sg.Menu(
                [
                    [
                        'Settings',
                        [
                            'Pick Color Theme',
                            [
                                'Dark Blue::-DARKBLUE-',
                                'Default::-DEFAULT-',
                                'Dark Purple::-DARKPURPLE-'
                            ]
                        ]
                    ]
                ],
            )
        ],
        [
            # in order to have access to a scrollbar I need to use column
            sg.Column(
                [
                    [
                        graph
                    ]
                ],
                scrollable = True,
                vertical_scroll_only = True,
                size = (850, 550)
            )
        ],
        [
            # load all the buttons at the bottom: load, add, clear, save and run
            sg.B(
                'Load Input Deck',
                size = FOOTER_BUTTON_SIZE,
                key = '-LOAD-',
                pad = (1, 1)
            ),
            sg.B(
                'Add Processing Step',
                size = FOOTER_BUTTON_SIZE,
                key = '-ADD-',
                pad = (1, 1)
            ),
            sg.B(
                'Clear Steps',
                size = FOOTER_BUTTON_SIZE,
                key = '-CLEAR-',
                pad = (1, 1)
            ),
            sg.B(
                'Satisfy Variables',
                size = FOOTER_BUTTON_SIZE,
                key = '-VARIABLES-',
                pad = (1, 1)
            ),
            sg.B(
                'Save Input Deck',
                size = FOOTER_BUTTON_SIZE,
                key = '-SAVE-',
                pad = (1, 1)
            ),
            sg.B(
                'Submit Job',
                size = FOOTER_BUTTON_SIZE,
                key = '-RUN-',
                pad = (1, 1)
            )
        ]
    ]
    
    # create the window
    window_ = sg.Window('Pantry', layout=layout, finalize=True)
    if window is not None:
        window.close()
    return (window_, graph)
    
def load_cards_from_input_deck():
    """
    create a new window to ask the user to pick an input deck, read that input
    deck and export the cards to assembled deck
    """
    # create a gui window to load an input deck based on a file
    layout = [
        [
            sg.Input(key='-INP-'),
            sg.FileBrowse('Browse', file_types=(('Input Decks', '*.inp'),))
        ],
        [
            sg.OK(), sg.Cancel()
        ]
    ]
    
    # create the load window and close it once we get its info
    window = sg.Window('Load Input Deck').Layout(layout)
    event, values = window.read()
    window.Close()

    if event in (sg.WIN_CLOSED, 'Cancel'):
        return None

    if event == 'OK':
        if values['-INP-']:
            inp = read_input_deck(values['-INP-'])
            return inp.cards
    return None

    
def add_card_manually():
    """
    add cards manually
    """
    # create a gui window to add a card to the existing workflow
    layout = [
        [
            sg.T('Add Preprocessing Step'),
            sg.Combo(
                list(get_card_list(get_path_to_jsons()).keys()),
                key = '-COMBO-'
            )
        ],
        [
            sg.OK(), sg.Cancel()
        ]
    ]
    
    # create the window
    window = sg.Window('Add Preprocessing Step').Layout(layout)
    event, values = window.read()
    window.Close()
    
    if event == 'OK':
        if values['-COMBO-']:
            card = make_card(values['-COMBO-'].lower())
            return card
    return None

    
def save_input_deck(deck, filename):
    """
    save of the created pipeline/workflow

    :Parameters:
      -. `deck` : input_deck_reader.InputDeck obj, a picnic input deck
      -. `filename` : file-like str, the filename/path to to save
    """
    with open(filename, 'w') as f:
        _ = f.write('*start\n')
        _ = f.write('  *sink\n')
        _ = f.write('    ' + os.path.dirname(filename) + '\n')
        for card in deck.cards:
            line = ['  ' + card.cardname]
            for param in card.parameters.keys():
                line.append(param + '=' + card.parameters[param])
            _ = f.write(', '.join(line) + '\n')
            for dataline in card.datalines:
                _ = f.write('    ' + ', '.join(dataline) + '\n')
        _ = f.write('*end')
        
def show_parameters(card):
    """
    create a window to display the parameters and datalines for the selected
    card

    :Parameters:
      -. `card` : input_deck_reader.Card, an input deck card
    """
    # create the parameters column
    parameter_column = []
    for parameter in card.parameters.keys():
        parameter_column.append(
            [
                sg.Text(parameter.lower()),
                sg.Input(
                    card.parameters[parameter],
                    key = '-PM'+parameter+'-',
                    expand_x = True
                )
            ]
        )
    
    # create the datalines column
    dataline_column = []
    dataline_column.append([sg.B('+', key='-ADDDL-')])
    idx = 0
    for idx, dataline in enumerate(card.datalines):
        dataline_column.append(
            [
                sg.Input(dataline[0], key='-DL'+str(idx)+'-'),
                sg.FileBrowse()
            ]
        )
    
    # create layout of two columns, left = parameters, right = datalines
    layout = [
        [
            sg.Column(
                [
                    [
                        sg.Frame(
                            'Parameters',
                            parameter_column,
                            expand_x = True,
                            expand_y = True
                        )
                    ]
                ],
                expand_y = True
            ),
            sg.Column(
                [
                    [
                        sg.Frame(
                            'Datalines',
                            dataline_column,
                            key = '-DLFRAME-',
                            expand_x = True,
                            expand_y = True
                        )
                    ]
                ],
                expand_y = True
            )
        ],
        [
            sg.OK(), sg.Cancel(), sg.Button('Delete', key='-DELETE-')
        ]
    ]
    
    # create a window based on the layout just created
    window = sg.Window('Preprocessing Step Details').Layout(layout)
    while True:
        event, values = window.read()
        
        # when pressing OK, save the parameters and datalines
        if event == 'OK':
            parameters = {}
            datalines = []
            for parameter in values.keys():
                if parameter.startswith('-PM'):
                    parameters[parameter[3:-1]] = values[parameter]
                elif parameter.startswith('-DL'):
                    datalines.append(values[parameter])
            
            # create the window
            window.Close()
            
            return (parameters, [[d] for d in datalines])

        # add a dataline
        elif event == '-ADDDL-':
            idx += 1
            window.extend_layout(
                window['-DLFRAME-'],
                [
                    [
                        sg.Input('Pick a file', key='-DL'+str(idx)+'-'),
                        sg.FileBrowse()
                    ]
                ]
            )
        
        # cancel creating this card
        elif event in (sg.WIN_CLOSED, 'Cancel'):
            window.Close()
            return (None, None)
        
        # delete the card
        elif event == '-DELETE-':
            window.Close()
            return ('DELETE', None)
    
def create_variable_window(variables):
    """
    create a window to display the variable keys and the associated values

    :Parameters:
      -. `variables` : dict, variable keys
    """
    # build the layout
    layout = []
    for key in variables.keys():
        layout.append(
            [
                sg.Text(key),
                sg.Input(
                    variables[key],
                    key = '-VARI' + key + '-',
                    expand_x = True
                )
            ]
        )
    
    # add buttons
    layout.append(
        [
            sg.OK(), sg.Cancel()
        ]
    )
    
    # create a window based on the layout just created
    window = sg.Window('Variable Associations').Layout(layout)
    while True:
        event, values = window.read()
        
        # when pressing OK, save the variables
        if event == 'OK':
            new_variables = {}
            for key in values.keys():
                if key.startswith('-VARI'):
                    new_variables[key[5:-1]] = values[key]
            
            # create the window
            window.Close()
            
            return (new_variables)
            
        elif event in (sg.WIN_CLOSED, 'Cancel'):
            window.Close()
            return None
    
def get_card_list(folder_path=None, extension='.json'):
    """
    return a list of cards found in the `cards.default_parameters`
    sub-directory. We use this to determine which instances steps will be
    loaded.

    :Parameters:
      -. `folder_path` : a file-like string, the path to find the json files
      -. `extension` : a string, the file type to search for the cards

    :Return:
      -. a dictionary, cards and their associated picnic classes
    """

    # {key = 'card name' : val = CardName obj}
    # example {'camra' : picnic.cards.camra.Camra}
    card_instance_legend = {}

    # Get all the jsons in the default parameters folder
    if folder_path is None:
        folder_path = get_path_to_jsons()
    for json_ in folder_path.glob(f"*{extension}"):
        card_name = os.path.basename(json_).replace(extension, '').replace('_', ' ')
        # skip sink, it is a special card that does not have a module
        if card_name == 'sink':
            continue
        module_ = importlib.import_module(
            # '.'.join(('picnic', 'cards', card_name.replace(' ', '_')))
            '.'.join(('cards', card_name.replace(' ', '_')))
        )
        card_instance_legend[card_name] = getattr(
            module_,
            ''.join([s.capitalize() for s in card_name.split(' ')])
        )

    return card_instance_legend

# =======================================
# Main
if __name__ == '__main__':
    # initialize the deck and main window
    deck = Deck()
    window, graph = create_main_window(deck, COLORTHEMES[THEME_IDX])
    
    # read the window and control flow based off the detected event/value
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
        
        # load an input deck
        if event == '-LOAD-':
            cards = load_cards_from_input_deck()
            if not cards is None:
                for card in cards:
                    if card.cardname.lower() != 'sink':
                        deck.add_card(card)
                window, graph = create_main_window(deck, COLORTHEMES[THEME_IDX], window)
                deck.build_graph_element(graph)
        
        # add a preprocessing step to the workflow
        elif event == '-ADD-':
            card = add_card_manually()
            if not card is None:
                deck.add_card(card)
                window, graph = create_main_window(deck, COLORTHEMES[THEME_IDX], window)
                deck.build_graph_element(graph)
        
        # clear all the steps
        elif event == '-CLEAR-':
            deck.clear_cards()
            window, graph = create_main_window(deck, COLORTHEMES[THEME_IDX], window)
            deck.build_graph_element(graph)
        
        # if any variables have been added, satisfy them
        elif event == '-VARIABLES-':
            deck.satisy_variables()
        
        # save the input deck
        elif event == '-SAVE-':
            filename = sg.popup_get_file('Choose Save File', save_as=True)
            if filename:
                save_input_deck(deck, filename)
        
        # clicking on the canvas
        elif event == '-CANVAS-':
            card_idx = values['-CANVAS-'][1]//(CARD_SIZE[1]+PADDING)
            # check to make sure the user has actually clicked a card and not 
            #   some padding
            if not card_idx >= len(deck.cards):
                deck.build_graph_element(graph, card_idx) # highlight card
                card = deck.cards[card_idx]
                
                parameters, datalines = show_parameters(card)
                if not (parameters, datalines)==(None, None):
                    if parameters == 'DELETE':
                        deck.remove_card(card_idx)
                    else:
                        deck.cards[card_idx].parameters = parameters
                        deck.cards[card_idx].datalines = datalines
                
                deck.build_graph_element(graph)
        
        elif event == '-RUN-':
            sg.popup('This feature has been disabled')
        
        # change the color theme
        elif event == 'Dark Blue::-DARKBLUE-':
            THEME_IDX = 0
            window, graph = create_main_window(deck, COLORTHEMES[THEME_IDX], window)
            deck.build_graph_element(graph)
        elif event == 'Default::-DEFAULT-':
            THEME_IDX = 1
            window, graph = create_main_window(deck, COLORTHEMES[THEME_IDX], window)
            deck.build_graph_element(graph)
        elif event == 'Dark Purple::-DARKPURPLE-':
            THEME_IDX = 2
            window, graph = create_main_window(deck, COLORTHEMES[THEME_IDX], window)
            deck.build_graph_element(graph)
        else:
            print(event, values)
