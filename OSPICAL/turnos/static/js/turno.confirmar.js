confirmar = {
	afiliado: false,
	turnos: [],
	buscar: function(numero) {
		var url = "/json/afiliado/numero/{0}/".format(numero);
		$.getJSON(url, function(data) {
			if (data.length > 0) {
				confirmar.afiliado = new Afiliado(data[0]);
				confirmar.cargar();
			} else if (data.length > 1){
				mostrarMensaje(MESSAGE_NUMERO_DUPLICADO,{type:'warning'});
			} else {
				mostrarMensaje(MESSAGE_NUMERO_INEXISTENTE_DESCRIPCION,
						{title:MESSAGE_NUMERO_INEXISTENTE_TITLE});
			}
		});
	},
	cargar: function() {
		var url = "/json/turnos/afiliado/{0}/".format(confirmar.afiliado.id);
		var destino = $('#id_turnos');
		$.getJSON(url, function(data) {
			if(data.length > 0) {
				var options = data.length > 1 ?
							  "<option value='{0}'>{1}</option>".format(0,DEFAULT_MESSAGE): 
							  "";
				$.each(data,function(index, value){
					confirmar.turnos.push(value);
					options += '<option value="{0}">{1} &lt;{2}&gt;</option>'.format(value.id,
																			 value.especialidad,
																			 value.especialista);
				});
				destino.empty().append(options);
				destino.focus();
				// Si es la unica opcion, la selecciono, llamo al evento y avanzo al siguiente paso
				if(data.length == 1) {
					$('#id_turnos option:eq(1)').prop('selected', true);
					changeTurno();
				}
			} else {
				mostrarMensaje(MESSAGE_SIN_TURNOS_RESERVADOS_HOY,
						{title:MESSAGE_SIN_TURNOS_RESERVADOS_HOY_TITLE})
			}
		});
	},
	mostrarDatosReserva: function(id) {
		reserva = this.__obtenerReserva(id);
		fecha_r = new Date(reserva.fecha_reserva * 1000);
		consultorio = reserva.consultorio ? reserva.consultorio : MESSAGES_NO_ASIGNADO;
		$('#id_info').show();
		$('#id_nya').text("{0} {1}".format(confirmar.afiliado.nombre, confirmar.afiliado.apellido));
		$.datepicker.setDefaults($.datepicker.regional["es"])
		$('#id_fecha_r').text($.datepicker.formatDate("DD dd 'de' MM", fecha_r));
		$('#id_consultorio').text(consultorio);
	},
	__obtenerReserva: function(id) {
		var found = false;
		var i = -1;
		var length = confirmar.turnos.length;
		while (!found && i < length) {
			i++;
			found = id == confirmar.turnos[i].id;
		}
		return found ? confirmar.turnos[i] : null;
	},
}

function changeNumero(){
	var numero = $('#id_numero').data('mask').getCleanVal();
	confirmar.buscar(numero);
}

function changeTurno() {
	var id = parseInt($('#id_turnos').val());
	if(id)
		confirmar.mostrarDatosReserva(id);
}

$(document).ready(function(){
	$('#id_info').hide();
	$('#id_numero').mask('0000 0000 0000');
	$('#id_numero').blur(changeNumero);
	$('#id_turnos').change(changeTurno);
	$("#id_numero").keypress(function(e) {
		if(e.which == 13) {
	    	e.preventDefault()
	    	$("#id_turnos").focus();
	    }
	});
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