var afiliado;
var turnos;

function buscarAfiliado(numero){
	var url = "/json/afiliado/numero/{0}/".format(numero);
	$.getJSON(url, function(data) {
		if (data.length > 0) {
			afiliado = new Afiliado(data[0]);
			$('#id_info').show();
			$('#id_nya').text("{0} {1}".format(afiliado.nombre, afiliado.apellido));
		} else if (data.length > 1){
			mostrarMensaje(MESSAGE_NUMERO_DUPLICADO,{type:'warning'});
		} else {
			mostrarMensaje(MESSAGE_NUMERO_INEXISTENTE_DESCRIPCION,
					{title:MESSAGE_NUMERO_INEXISTENTE_TITLE});
		}
	})
}

function cargarTurnos() {
	var url = "/json/turnos/afiliado/{0}/".format(afiliado.numero);
	var destino = $('#id_turnos');
	$.getJSON(url, function(data) {
		if(data.length > 0) {
			var options = "<option value='{0}'>{1}</option>".format(0,DEFAULT_MESSAGE);
			$.each(data,function(index, value){
				options += '<option value="{0}">{1} - {2}</option>'.format(value.id,
																		 value.especialidad,
																		 value.especialista);
			});
			destino.empty().append(options);
			destino.focus();
		}
	});
}

function changeNumero(){
	var numero = $('#id_numero').data('mask').getCleanVal();
	buscarAfiliado(numero)
	cargarTurnos();
}

function changeTurno() {
	url = "/json/"
	$.getJSON(url, function(data) {
		this.presentismo = data.presentismo_ok;
		if(!this.presentismo)
			mostrarMensaje(MESSAGE_PRESENTISMO, {type:'information'});
	});
}

$(document).ready(function(){
	$('#id_info').hide();
	$('#id_numero').mask('0000 0000 0000');
	$('#id_numero').change(changeNumero);
	$('#id_turno').change(changeTurno);
	$('form').submit(function() {
		$('#id_numero').unmask();
	});
	$('form').validate({
		rules: {
			numero:{
				required:true,
			},
			afiliado:{
				required:true,
				number:true,
			},
			turnos:{
				required:true,
				number:true,
			},
		},
	});
	
});