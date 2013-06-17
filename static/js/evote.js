var uls=[];
jQuery('.model-ranking').attr('readonly',true).each(function(){var ul=jQuery(this).closest('ul'); ul.find('li').addClass('ranking-option'); if(uls.indexOf(ul)<0) uls.push(ul); }); 
for(var k=0; k<uls.length; k++) uls[k].sortable({stop:function(){jQuery(this).find('input.model-ranking').each(function(i){jQuery(this).val(i+1);})} });

