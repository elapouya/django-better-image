/*!
 * django-better-image javascript for widget
 * https://github.com/elapouya/django-better-image
 *
 * Copyright 2019, Eric Lapouyade
 * Released under the LGPL license
 */
(function ( $ ) {

    var csrftoken = Cookies.get('csrftoken');

    function betterImageCropDialog(widget_container, image_url, handler) {
        // set message
        const modal = $("#BetterImageCropDialogModal");
        const submit_button = $('#BetterImageCropDialogModal .crop-save-button');
        const img_elt = widget_container.find('.upload-image');
        const preview = widget_container.find('.crop-preview');
        let aspect_ratio = widget_container.attr('data-aspect-ratio');
        aspect_ratio = (aspect_ratio === 'None') ? NaN : parseFloat(aspect_ratio);
        let autocrop_area = widget_container.attr('data-autocrop-area');
        autocrop_area = (autocrop_area === 'None') ? 0 : parseInt(autocrop_area) / 100;
        let cropper = null;

        function fit_to_container(cropper) {
            let adata = cropper.getCanvasData();
            const cdata = cropper.getContainerData();
            adata.height = adata.height * cdata.width / adata.width;
            adata.width = cdata.width;
            adata.left = 0;
            adata.top = (cdata.height - adata.height) / 2;
            if (adata.height > cdata.height) {
                adata.width = adata.width * cdata.height / adata.height;
                adata.height = cdata.height;
                adata.top = 0;
                adata.left = (cdata.width - adata.width) / 2;
            }
            const shrink_by = cropper.options.autoCropArea;
            cropper.setCanvasData({
                top: adata.top,
                left: adata.left,
                width: adata.width,
                height: adata.height
            });
            cropper.setCropBoxData({
                top: adata.top + adata.height * (1 - shrink_by) / 2,
                left: adata.left + adata.width * (1 - shrink_by) / 2,
                height: adata.height * shrink_by,
                width: adata.width * shrink_by
            });
        }

        function zoom_to_crop_box(cropper, ratio) {
            const adata = cropper.getCanvasData();
            const cdata = cropper.getContainerData();
            let bdata = cropper.getCropBoxData();
            if (bdata.width === undefined) bdata = {
                top: 0, left: 0, width: cdata.width, height: cdata.height
            };
            let ax = adata.left + adata.width / 2;
            let ay = adata.top + adata.height / 2;
            let bx = bdata.left + bdata.width / 2;
            let by = bdata.top + bdata.height / 2;
            let cx = cdata.width / 2;
            let cy = cdata.height / 2;
            let delta_bx = cx - bx;
            let delta_by = cy - by;
            let delta_ax = cx - ax;
            let delta_ay = cy - ay;

            cropper.options.viewMode = 0;

            cropper.setCanvasData({
                top: cy - delta_ay * ratio - adata.height * ratio / 2 + delta_by * ratio,
                left: cx - delta_ax * ratio - adata.width * ratio / 2 + delta_bx * ratio,
                height: adata.height * ratio,
                width: adata.width * ratio
            });

            cropper.setCropBoxData({
                top: cy - (bdata.height * ratio / 2),
                left: cx - (bdata.width * ratio / 2),
                height: bdata.height * ratio,
                width: bdata.width * ratio
            });

            cropper.options.viewMode = 1;

        }

        modal.find("div.modal-body-crop").html(
            '<img class="pic-to-edit" src="' + image_url + '">');

        $("#BetterImageCropDialogModal").on("shown.bs.modal", function () {
            var img = modal.find("img.pic-to-edit");
            img.cropper({
                viewMode: 1,
                aspectRatio: aspect_ratio,
                autoCropArea: autocrop_area,
                autoCrop: (autocrop_area !== 0)
            });

            cropper = img.data('cropper');

            img.on('cropstart', function () {
                submit_button.text(submit_button.attr('data-crop-label'));
            });

            function cropper_orientation_change() {
                cropper.destroy();
                cropper.init();
            }

            if (window._prev_cropper_orientation_change_listener)
                window.removeEventListener(
                    "orientationchange",
                    window._prev_cropper_orientation_change_listener,
                    false);
            window.addEventListener(
                "orientationchange",
                cropper_orientation_change,
                false);
            window._prev_cropper_orientation_change_listener = cropper_orientation_change;

            function clear_cropbox() {
                submit_button.text(submit_button.attr('data-save-label'));
                cropper.clear();
            }

            // as modal dialog may used several times on the same time :
            // remove previous click event listner (off) before adding new one
            modal.find("div.action-group button").off('click').on('click', function () {
                const button = $(this);
                const action = button.attr('data-action');
                let data = cropper.getData();
                switch (action) {
                    case 'crop':
                        clear_cropbox();
                        cropper.setDragMode('crop');
                        modal.find('button[data-action="crop"]').removeClass('btn-default').addClass('btn-success');
                        modal.find('button[data-action="move"]').removeClass('btn-success').addClass('btn-default');
                        break;
                    case 'move':
                        clear_cropbox();
                        cropper.setDragMode('move');
                        modal.find('button[data-action="move"]').removeClass('btn-default').addClass('btn-success');
                        modal.find('button[data-action="crop"]').removeClass('btn-success').addClass('btn-default');
                        break;
                    case 'zoom-in':
                        zoom_to_crop_box(cropper, 1.5);
                        break;
                    case 'zoom-out':
                        zoom_to_crop_box(cropper, 1 / 1.5);
                        break;
                    case 'rotate-left':
                        cropper.options.viewMode = 0;
                        cropper.rotate(-90);
                        fit_to_container(cropper);
                        cropper.options.viewMode = 1;
                        break;
                    case 'rotate-right':
                        cropper.options.viewMode = 0;
                        cropper.rotate(90);
                        fit_to_container(cropper);
                        cropper.options.viewMode = 1;
                        break;
                    case 'flip-horizontal':
                        cropper.scaleX(-data.scaleX);
                        fit_to_container(cropper);
                        break;
                    case 'flip-vertical':
                        cropper.scaleY(-data.scaleY);
                        fit_to_container(cropper);
                        break;
                    case 'reset':
                        cropper.reset();
                        clear_cropbox();
                        break;
                }
            });
        });

        // reset submit button label to "save"
        submit_button.text(submit_button.attr('data-save-label'));

        //Trigger the modal
        $("#BetterImageCropDialogModal").modal({
            backdrop: 'static',
            keyboard: false
        });

        //Pass true to a callback function
        $("#BetterImageCropDialogModal .btn-yes").off('click').on('click', function () {
            if (cropper) {
                let data = cropper.getData();
                const img_data = cropper.getImageData();
                data.imgWidth = img_data.naturalWidth;
                data.imgHeight = img_data.naturalHeight;
                // Update the thumb by activating the preview
                // The preview is only activated here (preview takes a lot of cpu)
                if (preview) {
                    img_elt.addClass('hidden');
                    preview.removeClass('hidden');
                    if (!cropper.cropped) {
                        // if not cropped (save button) : need to activate the
                        // cropbox to have a correct preview
                        cropper.crop();
                        const adata = cropper.getCanvasData();
                        // set the cropbox to the full canvas
                        cropper.setCropBoxData({
                            top: adata.top,
                            left: adata.left,
                            width: adata.width,
                            height: adata.height
                        });
                    }
                    cropper.options.preview = preview;
                    cropper.initPreview();
                    cropper.preview();
                    // deactivate at once for further usage
                    cropper.options.preview = null;
                }
                handler(true, data);
            } else {
                handler(false, null);
            }
            $("#BetterImageCropDialogModal").modal("hide");
        });

        //Pass false to callback function
        $("#BetterImageCropDialogModal .btn-no").off('click').on('click', function () {
            handler(false, null);
            $("#BetterImageCropDialogModal").modal("hide");
        });
    }

    function betterImageWidgetInit(container) {
        const upload_button = container.find('.upload-button');
        const upload_button_present = (upload_button.length !== 0);
        const clear_button = container.find('.clear-button');
        const edit_button = container.find('.edit-button');
        const img = container.find('.upload-image');
        const img_data = container.find('.image-data');
        const img_thumb = container.find('img.thumb');
        const preview = container.find('.crop-preview');
        const file_input = container.find('.input-file');
        const drop_zone = container.find('.dropzone');
        const image_buttons = container.find('.image-buttons');
        const crop_on_upload = (container.attr('data-crop-on-upload') === 'True') ? true : false;
        const tooltip_template = '<div class="tooltip" role="tooltip"><div class="arrow"></div><div class="tooltip-inner better-image-widget"></div></div>';

        var uploaded_image = false;
        container.biw_tooltip = null;

        upload_button.on('click', function () {
            file_input.val('');
            file_input.click();

            return false;
        });

        function display_confirm_tooltip(container) {
            setTimeout(function () {
                container.biw_tooltip.tooltip('show');
                setTimeout(function () {
                    container.biw_tooltip.tooltip('hide');
                    container.biw_tooltip.tooltip('dispose');
                    container.biw_tooltip = null;
                }, 3000);
            }, 300);
        }

        function add_saved_tooltip(container, selector) {
            const msg = container.attr('data-saved-tooltip');
            if (msg) {
                const image = container.find(selector).first();
                container.biw_tooltip = container.tooltip({
                    title: msg,
                    placement: 'right',
                    delay: {"show": 1000, "hide": 1000},
                    template: tooltip_template
                });
                image.on('load', function () {
                    display_confirm_tooltip(container);
                });
            }
        }

        function add_cleared_tooltip(container) {
            const msg = container.attr('data-cleared-tooltip');
            if (msg) {
                container.biw_tooltip = container.tooltip({
                    title: msg,
                    placement: 'right',
                    delay: {"show": 1000, "hide": 1000},
                    template: tooltip_template
                });
                display_confirm_tooltip(container);
            }
        }

        function add_remember_tooltip(container) {
            const msg = container.attr('data-remember-tooltip');
            if (msg) {
                console.log('create tooltip...');
                container.biw_tooltip = container.tooltip({
                    title: msg,
                    placement: 'right',
                    delay: {"show": 1000, "hide": 1000},
                    template: tooltip_template
                });
                display_confirm_tooltip(container);
            }
        }

        clear_button.on('click', function () {
            if (upload_button_present) {
                image_buttons.addClass('hidden');
                img.addClass('hidden');
                preview.addClass('hidden');
                // clear file input field
                file_input.val('');
                // show upload button
                upload_button.show()
            } else {
                if (container.biw_tooltip) {
                    container.biw_tooltip.tooltip('dispose');
                }
                let confirm_msg = clear_button.attr('data-confirm-msg');
                if (!confirm_msg) confirm_msg = 'Do you confirm ?';
                bootstrapConfirmDialog(confirm_msg, function (ok) {
                    if (ok) {
                        data = {
                            csrfmiddlewaretoken: csrftoken,
                            upload_params: container.attr("data-upload-params"),
                            upload_params_chk: container.attr("data-upload-params-chk")
                        };
                        url = clear_button.attr('data-post-url');
                        $.post(url, data, function (response) {
                            new_container = $(response.replace_html);
                            container.replaceWith(new_container);
                            betterImageWidgetInit(new_container);
                            add_cleared_tooltip(new_container);
                        });
                    }
                });
            }
            return false;
        });

        edit_button.on('click', function () {
            if (upload_button_present) {
                betterImageCropDialog(container, img.attr('src'), function (ok, data) {
                    if (ok) {
                        img_data.val(JSON.stringify(data));
                        add_remember_tooltip(container);
                    }
                });
            } else {
                if (container.biw_tooltip) {
                    container.biw_tooltip.tooltip('dispose');
                }
                const image_url = img_thumb.attr('data-image-url');
                betterImageCropDialog(container, image_url, function (ok, data) {
                    if (ok) {
                        data = $.extend(data, {
                            csrfmiddlewaretoken: csrftoken,
                            upload_params: container.attr("data-upload-params"),
                            upload_params_chk: container.attr("data-upload-params-chk")
                        });
                        url = edit_button.attr('data-post-url');
                        const loading_msg = img_thumb.attr('data-img-processing');
                        img_thumb.loading({message: loading_msg});
                        $.post(url, data, function (response) {
                            img_thumb.loading('stop');
                            new_container = $(response.replace_html);
                            container.replaceWith(new_container);
                            betterImageWidgetInit(new_container);
                            add_saved_tooltip(new_container, 'img.thumb');
                        });
                    }
                });
            }
            return false;
        });

        file_input.on('change', function (e) {
            let duration = (uploaded_image) ? 300 : 1;
            img.animate({opacity: 0}, duration);
            setTimeout(function () {
                let i = 0;
                for (i = 0; i < e.originalEvent.srcElement.files.length; i++) {
                    let file = e.originalEvent.srcElement.files[i],
                        reader = new FileReader();
                    reader.onloadend = function () {
                        uploaded_image = true;
                        img.attr('src', reader.result).animate({opacity: 1}, 700);
                        // reset cropping infos
                        img_data.val('');
                        // hide upload button
                        upload_button.hide()
                        // display edit/clear buttons
                        image_buttons.removeClass('hidden');
                        if (crop_on_upload) {
                            betterImageCropDialog(container, img.attr('src'), function (ok, data) {
                                img_data.val(JSON.stringify(data));
                                add_remember_tooltip(container);
                            });
                        } else {
                            add_remember_tooltip(container);
                        }
                    };
                    reader.readAsDataURL(file);
                    img.removeClass('hidden');
                    preview.addClass('hidden');

                }
            }, duration);
        });

        drop_zone.dropzone({
            url: drop_zone.attr('data-post-url'),
            paramName: container.attr("data-field-name"),
            timeout: 300000,
            thumbnailWidth: parseInt(container.attr('data-dz-thumb-width')),
            thumbnailHeight: parseInt(container.attr('data-dz-thumb-height')),
            sending: function (file, xhr, formData) {
                formData.append("csrfmiddlewaretoken", csrftoken);
                formData.append("upload_params", container.attr("data-upload-params"));
                formData.append("upload_params_chk", container.attr("data-upload-params-chk"));
            },
            success: function (file, response) {
                const new_container = $(response.replace_html);
                container.replaceWith(new_container);
                betterImageWidgetInit(new_container);
                add_saved_tooltip(new_container, 'img.thumb');
            }
        });

        img_thumb.on('drop', function (event) {
            event.preventDefault();
            event.stopPropagation();
            bootstrapAlert('Please clear image first');
        });
        img_thumb.on('dragover dragleave', function (event) {
            event.preventDefault();
            event.stopPropagation();
        });
    }

    $(document).ready(function () {
        $('.better-image-widget-container').each(function () {
            const container = $(this);
            betterImageWidgetInit(container);
        });
    });

}(jQuery));