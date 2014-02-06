cancelar = {
	afiliado: false,
	turnos: [],
	buscar: function(filtro) {
		this.afiliado = Afiliado.load(filtro);
		if (this.afiliado)
			this.cargar();
	},
	cargar: function() {
		var url = "/json/turnos/afiliado/{0}/".format(this.afiliado.id);
		var destino = $('#id_turnos');
		$.getJSON(url, function(data) {
			if(data.length > 0) {
				var options = data.length > 1 ?
							  "<option value='{0}'>{1}</option>".format(0,DEFAULT_MESSAGE): 
							  "";
				$.each(data,function(index, value){
					value.fecha_turno = new Date(value.fecha_turno*1000);
					cancelar.turnos.push(value);
					$.datepicker.setDefaults($.datepicker.regional["es"])
					fecha = $.datepicker.formatDate("dd 'de' MM", value.fecha_turno);
					options += '<option value="{0}">{1} - {2} &lt;{3}&gt;</option>'.format(
								value.id,
								fecha,
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
		$.datepicker.setDefaults($.datepicker.regional["es"])
		$('#id_fecha_r').text($.datepicker.formatDate("dd 'de' MM", fecha_r));
		$('#id_nya').text("{0} {1}".format(this.afiliado.nombre, this.afiliado.apellido));
		$('#id_consultorio').text(consultorio);
		$('#id_info').show();
	},
	__obtenerReserva: function(id) {
		var found = false;
		var i = -1;
		var length = this.turnos.length;
		while (!found && i < length) {
			i++;
			found = id == this.turnos[i].id;
		}
		return found ? this.turnos[i] : null;
	},
}
function changeNumero(){
	var numero = $('#id_numero').data('mask').getCleanVal();
	cancelar.buscar({numero:numero});
}
function changeDNI(){
	var dni = $('#id_dni').val();
	cancelar.buscar({dni:dni});
}
function changeTurno() {
	var id = parseInt($('#id_turnos').val());
	if(id) {
		cancelar.mostrarDatosReserva(id);
		$('#id_motivo').focus();
	}
}
$(document).ready(function(){
	$('#id_info').hide();
	$('#id_numero').mask('0000 0000 0000');
	$('#id_dni').number(true, 0,',','.');
	$('#id_dni').blur(changeDNI);
	$('#id_numero').blur(changeNumero);
	$('#id_turnos').change(changeTurno);
	$("#id_numero, #id_dni").keypress(function(e) {
		if(e.which == 13) {
	    	e.preventDefault()
	    	$("#id_turnos").focus();
	    }
	});
	$('form').submit(function() {
		$('#id_dni').number(true,0,'','');
		$('#id_numero').unmask();
	});
	$('form').validate({
		rules: {
			dni:{
				required:true,
			},
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