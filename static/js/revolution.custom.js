// Slider revolution
// Plugin Options
jQuery.noConflict();
jQuery(document).ready(function($) {
	if ($.fn.cssOriginal!=undefined)
		$.fn.css = $.fn.cssOriginal;

	$('.banner').revolution({
		delay:9000,
		
		startwidth:940,
                startheight:400,
		thumbWidth:100,
		thumbHeight:50,
		thumbAmount:5,

		onHoverStop:"on",
		hideThumbs:200,
		navigationType:"bullet",
		navigationStyle:"round",
		navigationArrows:"verticalcentered",

		touchenabled:"on",

		navOffsetHorizontal:0,
		navOffsetVertical:10,
		shadow:1,
		fullWidth:"off"
	});
});
					
