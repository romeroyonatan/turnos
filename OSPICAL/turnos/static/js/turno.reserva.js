$(document).ready(function(){
	var ajax = $.ajax({
		url:"/static/js/templates/reservarturno.template.html",
		async: false});
	
	// TODO: Reconstruir lista cuando tenga algo
	l = new Lista($('#id_turnos'),{template:ajax.responseText});

	$("#id_dni").blur(function() {
		var container = $("#id_dni");
		var dni = container.val();
		if(/\d+/.test(dni)) {
			url = '/json/afiliado/dni/{0}/'.format(dni);
			$.getJSON(url, function(data) {
				if (data.length == 1) {
					var a = new Afiliado(data[0]);
				} else if (data.length > 1) {
					mostrarMensaje(MESSAGE_DNI_DUPLICADO_DESCRIPCION, 
							   {title:MESSAGE_DNI_DUPLICADO_TITLE, type:'warning'});
				} else {
					mostrarMensaje(MESSAGE_DNI_INEXISTENTE_DESCRIPCION,
							{title:MESSAGE_DNI_INEXISTENTE_TITLE, element:container});
				}
			});
		}
	});
	
	$("#id_numero").blur(function() {
		var container = $("#id_numero");
		var value = container.data('mask').getCleanVal();;
		if(/\d+/.test(value)) {
			url = '/json/afiliado/numero/{0}/'.format(value);
			$.getJSON(url, function(data) {
				if (data.length == 1){
					new Afiliado(data[0]);
				} else if (data.length > 1){
					mostrarMensaje(MESSAGE_NUMERO_DUPLICADO,{type:'warning'});
				} else {
					mostrarMensaje(MESSAGE_NUMERO_INEXISTENTE_DESCRIPCION,
							{title:MESSAGE_NUMERO_INEXISTENTE_TITLE, element:container});
				}
			});
		}
	});

	function cambiaEspecialidad() {
		$("#id_especialista, #id_dia, #id_hora").prop('disabled', true);
		var id = $("#id_especialidad").val();
		if(!id)
			return;
		var url = '/json/especialistas/especialidad/{0}/'.format(id);
		var destino = $('#id_especialista');
		$.getJSON(url, function(data) {
			if(data.length > 0) {
				destino.removeAttr('disabled');
				var options = "<option value='{0}'>{1}</option>".format(0,DEFAULT_MESSAGE);
				$.each(data,function(index, value){
					options += '<option value="{0}">{1}, {2}</option>'.format(value.id,
																			 value.apellido,
																			 value.nombre);
				});
				destino.empty().append(options);
				destino.focus();
				if(data.length == 1) {
					$('#id_especialista option:eq(1)').prop('selected', true);
					cambiaEspecialista();
				}
			}
		});
	}
	
	function cambiaDia() {
		$("#id_hora").prop({disabled: true});
		var milis = parseInt($("#id_dia").val());
		var id = $("#id_especialidad").val();
		if(!id || !milis)
			return;
		var d = new Date(milis);
		var url = '/json/turnos/{0}/{1}/{2}/{3}/'.format(id, d.getFullYear(),d.getMonth()+1,d.getDate());
		var destino = $('#id_hora');
		$.getJSON(url, function(data) {
			if(data.length > 0) {
				destino.removeAttr('disabled');
				var options = "<option value='{0}'>{1}</option>".format(0,DEFAULT_MESSAGE);
				$.each(data,function(index, value){
					fecha = new Date(value.fecha * 1000)
					options += '<option value="{0}">{1}:{2}</option>'.format(value.id, 
																			 n(fecha.getHours()),
																			 n(fecha.getMinutes()));
				});
				destino.empty().append(options);
				destino.focus();
			} else {
				mostrarMensaje(MESSAGE_NO_TURNOS);
			}
		});
	}
	
	function cambiaEspecialista() {
		$("#id_dia, #id_hora").prop({disabled: true});
		var id = $("#id_especialista").val();
		if(!id)
			return;
		var url = '/json/turnos/{0}/'.format(id);
		var destino = $('#id_dia');
		$.getJSON(url, function(data) {
			if(data.length > 0) {
				destino.removeAttr('disabled');
				var options = "<option value='{0}'>{1}</option>".format(0,DEFAULT_MESSAGE);
				$.each(data,function(index, value){
					var estado = ESTADOS[value.estado] ? "["+ESTADOS[value.estado]+"] " : "";
					var milis = value.fecha * 1000;
					var fecha = new Date(milis)
					options += '<option value="{0}">{4}{1}, {2} de {3}</option>'.format(milis, 
																					 DIA[fecha.getDay()],
																					 fecha.getDate(),
																					 MES[fecha.getMonth()],
																					 estado);
				});
				destino.empty().append(options);
				destino.focus();
				if(data.length == 1) {
					$('#id_dia option:eq(1)').prop('selected', true);
					cambiaDia();
				}
			} else {
				mostrarMensaje(MESSAGE_NO_DIAS);
			}
		});
	}
	
	$("#id_especialidad").change(cambiaEspecialidad);
	$("#id_especialista").change(cambiaEspecialista);
	$("#id_dia").change(cambiaDia);
	
	$("#id_hora").change(function(e) {
		var destino = $('#id_agregar');
		destino.focus();
	});
	
	$("#id_agregar").click(function() {
		var turno = {};
		turno['id'] = $("#id_hora").val();
		if(turno.id) {
			turno['especialidad'] = $("#id_especialidad option:selected").text();
			turno['especialista'] = $("#id_especialista option:selected").text();
			turno['dia'] = $("#id_dia option:selected").text();
			turno['hora'] = $("#id_hora option:selected").text();
			if(!l.add(turno)) {
				mostrarMensaje(MESSAGE_TURNO_YA_AGREGADO);
			}
			$(":submit").focus();
		} else {
			mostrarMensaje(MESSAGE_TURNO_NO_SELECCIONADO,{element:$('#id_hora')});
		}
	});
	
	$(':reset').click(function(){
		$('#tabla_turnos > tbody > tr').remove();
		$('#id_turnos, #id_afiliado').val('');
		$("#id_especialista, #id_dia, #id_hora").prop({disabled: true});
	});
	
	$("#id_dni, #id_numero").keypress(function(e) {
		if(e.which == 13) {
	    	e.preventDefault()
	    	$("#id_telefono").focus();
	    }
	});
	
	$('#id_dni').number(true, 0,',','.');
	$('#id_numero').mask('0000 0000 0000');
	
	$('form').submit(function() {
		$('#id_dni').number(true,0,'','');
		$('#id_numero').unmask();
	});
	
	$('form').validate({
		rules: {
			numero: "required",
			dni: "required",
			telefono: "required",
		},
		messages: {
			numero: "Debe ingresar el número de afiliado",
			dni: "Debe ingresar el DNI",
			telefono: "Debe ingresar un telefono",
		}
	});
});