
from django.shortcuts import render, redirect
from django.http import FileResponse
from django.contrib import messages
from PIL import Image
import io

def resizeimage(request):
    if request.method == 'POST':
        try:
            uploaded_image = request.FILES.get('image')
            if not uploaded_image:
                messages.error(request, 'Please upload an image.')
                return redirect('resizeimage')
                
            img = Image.open(uploaded_image)
            img_format = img.format
            output_format = request.POST.get('format', 'original')
            
            if output_format != 'original':
                if output_format == 'jpg':
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        img = img.convert('RGB')
                    img_format = 'JPEG'
                elif output_format == 'png':
                    img_format = 'PNG'
                elif output_format == 'webp':
                    img_format = 'WEBP'
            
            size_type = request.POST.get('sizeType')
            
            if size_type == 'preset':
                preset_size = request.POST.get('presetSize')
                preset_sizes = {
                    'passport': (1024, 1536),
                    'profile': (500, 500),
                    'square': (1080, 1080),
                    '3x4': (1200, 1800),
                    '4x6': (1600, 2400),
                    '5x7': (2000, 2800),
                    'A4': (2480, 3508),
                    'hd': (1920, 1080),
                    'facebook': (1640, 856),
                    'twitter': (1500, 500),
                    'linkedin': (1584, 396)
                }
                width, height = preset_sizes.get(preset_size, (800, 600))
            else:
                try:
                    width = int(request.POST.get('width', 0))
                    height = int(request.POST.get('height', 0))
                    if width <= 0 or height <= 0:
                        messages.error(request, 'Please enter valid dimensions greater than zero.')
                        return redirect('resizeimage')
                except (ValueError, TypeError):
                    messages.error(request, 'Please enter valid numeric dimensions.')
                    return redirect('resizeimage')

            resized_img = img.resize((width, height), Image.LANCZOS)
            buffer = io.BytesIO()
            
            if img_format == 'JPEG':
                resized_img.save(buffer, format=img_format, quality=90)
            else:
                resized_img.save(buffer, format=img_format)
                
            buffer.seek(0)
            messages.success(request, 'Image resized successfully!')

            if img_format == 'JPEG':
                extension = 'jpg'
            else:
                extension = img_format.lower()
            if not extension:
                extension = 'png'
                
            filename = f'resized_image.{extension}'

            response = FileResponse(
                buffer, 
                as_attachment=True, 
                filename=filename
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('resizeimage')

    return render(request, 'resizeimage.html')
