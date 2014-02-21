cancelar = {
	getEspecialista: function(especialidad_id) {
		var url = '/json/especialistas/especialidad/{0}/'.format(especialidad_id);
		var destino = $('#id_especialista');
		$.getJSON(url, function(data) {
			if(data.length > 0) {
				destino.removeAttr('disabled');
				var options = "";
				$.each(data,function(index, value){
					options += '<option value="{0}">{1}, {2}</option>'.format(value.id,
																			 value.apellido,
																			 value.nombre);
				});
				destino.empty().append(options);
				destino.focus();
				if(data.length == 1) {
					$('#id_especialista option:eq(0)').prop('selected', true);
					changeEspecialista();
				}
			} else {
				mostrarMensaje(MESSAGE_NO_ESPECIALISTAS_DESCRIPCION,{title:MESSAGE_NO_ESPECIALISTAS_TITLE});
			}
		});
	},
	getFecha: function(especialista_id) {
		var url = '/json/turnos/{0}/'.format(especialista_id);
		var destino = $('#id_fecha');
		$.getJSON(url, function(data) {
			if(data.length > 0) {
				destino.removeAttr('disabled');
				var options = '<option value="">{0}</option>'.format(DEFAULT_MESSAGE);
				$.each(data,function(index, value){
					var milis = value.fecha * 1000;
					var fecha = new Date(milis)
					options += '<option value="{0}">{4}{1}, {2} de {3}</option>'.format(
							milis, 
							DIA[fecha.getDay()],
							fecha.getDate(),
							MES[fecha.getMonth()],
							value.estado == 'X' ? '[{0}] '.format(ESTADOS[value.estado]) : "");
				});
				destino.empty().append(options);
				destino.focus();
			} else {
				mostrarMensaje(MESSAGE_NO_DIAS);
			}
		});
	},
	getReservas: function(especialidad_id, especialista_id, fecha) {
		var url = "/json/reservas/{0}/{1}/{2}/{3}/{4}/".format(especialidad_id,
															  especialista_id,
															  fecha.getFullYear(),
															  fecha.getMonth()+1,
															  fecha.getDate());
		$.getJSON(url, function(data) {
			if(data.length > 0) {
				cancelar.__mostrar_reservas(data);
			} else {
				$('#id_messages').text(MESSAGE_NO_RESERVAS);
			}
		});
	},
	__mostrar_reservas: function(data) {
		destino = $('#id_table_reservas > tbody');
		rows = '';
		$.each(data, function(index, value){
			fecha_turno = new Date(value.fecha_turno * 1000);
			fecha_reserva = new Date(value.fecha_reserva * 1000);
			$.datepicker.setDefaults($.datepicker.regional["es"])
			fecha_reserva = $.datepicker.formatDate("dd 'de' MM", fecha_reserva);
			fecha_turno = " {0}:{1}".format(fecha_turno.getHours(),
									        fecha_turno.getMinutes());
			rows += '<tr><td>{0}</td><td>{1}</td><td>{2}</td>\
				     <td>{3}</td><td>{4}</td></tr>'.format(
					fecha_turno,
					fecha_reserva,
					value.numero,
					value.afiliado,
					value.telefono);
		});
		destino.empty().append(rows);
		$('#id_lista_reservas').show();
		$('#id_messages').text(MESSAGE_RESERVAS.format(data.length));
	},
}
function changeEspecialidad(){
	var especialidad = $('#id_especialidad').val();
	cancelar.getEspecialista(especialidad);
}
function changeEspecialista(){
	var especialista = $('#id_especialista').val();
	cancelar.getFecha(especialista);
}
function changeFecha() {
	var especialidad_id = $('#id_especialidad').val();
	var especialista_id = $('#id_especialista').val();
	var fecha = new Date(parseInt($('#id_fecha').val()));
	$('#id_lista_reservas').hide();
	cancelar.getReservas(especialidad_id, especialista_id, fecha);
}
$(document).ready(function(){
	$('#id_lista_reservas').hide();
	$('#id_especialidad').change(changeEspecialidad);
	$('#id_especialista').change(changeEspecialista);
	$('#id_fecha').change(changeFecha);
	$("#id_especialidad, #id_especialista").keypress(function(e) {
		if(e.which == 13) {
	    	e.preventDefault()
	    	$("#id_fecha").focus();
	    }
	});
	$('form').validate({
		rules: {
			especialista:{
				required:true,
			},
			especialidad:{
				required:true,
			},
			fecha:{
				required:true,
			},
		},
	});
	
});