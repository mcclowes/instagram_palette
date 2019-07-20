# this code is messy but i'm feeling lazy. don't judge

import os, datetime, re, random, numpy, operator, cv2, colorsys
from sklearn.cluster import KMeans
from PIL import Image, ImageDraw

# settings
DEBUG = False
COLOR_BG = True
PALETTE_HEIGHT = 168
PALETTE_SIZE = 5
MARGIN = 40
OFFSET = 208

def getBrightness(color):
  r, g, b = color
  h, s, v = colorsys.rgb_to_hsv(r,g,b)
  return v

def sortColors(colors):
  if(DEBUG):
    print(colors)
    print(sorted(colors, key=lambda color: getBrightness(color), reverse=True))
  # sort by brightness
  return sorted(colors, key=lambda color: getBrightness(color), reverse=True)

def extractColors(image, n):
  # reshape image into a list of pixels
  px_list = image.reshape((image.shape[0] * image.shape[1], 3))

  # run kmeans function
  clt = KMeans(n_clusters = n)
  clt.fit(px_list)

  # get list of cluster colors
  clus_colors = clt.cluster_centers_.astype("uint8").tolist()
  clus_colors = sortColors(clus_colors)

  return clus_colors

def createBackgroundImage(colorPalette):
  r, g, b = [255, 255, 255]
  if(COLOR_BG==True):
    r, g, b = colorPalette[0]
  return Image.new("RGB", (1080,1080),(r, g, b))

def convertImages(input_files):
  # for every image in file list
  for i in input_files:
    if i == 'README.md':
      break

    # print state to terminal
    print("Converting " + i + '...')

    # open image and record size
    old_im = Image.open('input/' + i)
    old_im = old_im.convert('RGB')
    old_size = old_im.size
    old_x = old_size[0]
    old_y = old_size[1]

    # scale the image to have a 40 px buffer whether landscape or portrait
    scale = old_x/float(1000)
    small_y = int(old_y/scale)

    # if y axis is too big to provide enough room underneath for blur
    # set up image for portrait 'mode'
    if small_y > (960-PALETTE_HEIGHT):
      new_scale = old_y/float(1000)
      small_im = old_im.resize((int(old_x/new_scale),1000), Image.ANTIALIAS)
      aspect = "portrait"
      # if there won't be enough room to right of image for portrait mode blur
      # escape and provide warning message
      if small_im.size[0] > (960-PALETTE_HEIGHT):
        print("ya gonna have to crop this bad boi")
        break
    # else we're gonna be working in landscape
    else:
      small_im = old_im.resize((1000,small_y), Image.ANTIALIAS)
      aspect = "landscape"

    # get small_im into a cv2 compatible format
    image = numpy.array(small_im)

    # calculate color palette
    colorPalette = extractColors(image, PALETTE_SIZE)

    # create background image
    new_im = createBackgroundImage(colorPalette)

    # paste small_im onto background new_im
    new_im.paste(small_im,(MARGIN, MARGIN))
    draw = ImageDraw.Draw(new_im)

    # draw palette squares and fill with cluster colors
    if aspect == "landscape":
      for j in range(0, PALETTE_SIZE):
        left = MARGIN + (OFFSET * j)
        right = OFFSET * (j + 1)
        draw.rectangle([left, 872, right, 1040], fill=tuple(colorPalette[j]), outline=None)
    else:
      for j in range(0, PALETTE_SIZE):
        top = MARGIN + (OFFSET * j)
        bottom = OFFSET * (j + 1)
        draw.rectangle([872, top, 1040, bottom], fill=tuple(colorPalette[j]), outline=None)

    # get modified date of original photo - this allows the easy sorting of the
    # output files by age of the original
    mtime = os.path.getmtime(os.getcwd() + '/input/' + i)
    str_mtime = datetime.datetime.isoformat(datetime.datetime.fromtimestamp(mtime))
    str_mtime = re.sub("[^0-9.]", "-", str_mtime)

    # save the new image and prefix name with modified date
    new_im.save('output/' + str_mtime + '_' + i)

    # print state to terminal
    print(i + ' converted')

# create a list of all non-hidden files in input folder
def listdir_nohidden(path):
  for f in os.listdir(path):
    if not f.startswith('.'):
      yield f

# create list of images in "input" directory
input_files = listdir_nohidden(os.getcwd() + '/input')
convertImages(input_files)
