function cambiaDia() {
	$("#id_hora").prop({disabled: true});
	var milis = parseInt($("#id_dia").val());
	if(!milis)
		return;
	var d = new Date(milis*1000);
	var url = '/json/turnos/{0}/{1}/{2}/{3}/'.format(id, d.getFullYear(),d.getMonth()+1,d.getDate());
	var destino = $('#id_hora');
	$.getJSON(url, function(data) {
		if(data.length > 0) {
			destino.removeAttr('disabled');
			var options = "";
			$.each(data,function(index, value){
				fecha = new Date(value.fecha * 1000)
				options += '<option value="{0}">{1}:{2}</option>'.format(
						value.id, 
						n(fecha.getHours()),
						n(fecha.getMinutes()));
			});
			destino.empty().append(options);
			destino.focus();
			$('#id_hora option:eq(0)').prop('selected', true)
		} else {
			mostrarMensaje(MESSAGE_NO_TURNOS);
		}
	});
}


$(document).ready(function(){
	$("#id_dia").change(cambiaDia);
	$('form').validate({
		rules: {
			telefono: "required",
		},
	});
});