DEFAULT_MESSAGE = "Seleccionar";
MESSAGE_NO_DIAS = "El especialista no posee días disponibles para reservar turnos";
MESSAGE_NO_TURNOS = "No hay turnos disponibles este día";
MESSAGE_TURNO_YA_AGREGADO = "Ya agregó este turno";
MESSAGE_DNI_DUPLICADO = "DNI duplicado"
MESSAGE_DNI_INEXISTENTE = "DNI Inexistente"
DIA=["Domingo", "Lunes", "Martes", "Miercoles", "Jueves","Viernes","Sabado"];
MES=["enero", "febrero","marzo", "abril","mayo", "junio","julio","agosto","septiembre","octubre","noviembre","diciembre"];	
ESTADOS={C:"Completo",S:"Sobreturno"};

/**
 * Permite formatear una cadena como en C# mediante ubicadores posicionales
 * {0}{1}
 */
String.prototype.format = function () {
    var literal = this;
    for (var i = 0; i < arguments.length; i++) {
        var regex = new RegExp('\\{' + i + '\\}', 'g');
        literal = literal.replace(regex, arguments[i]);
    }
    return literal;
};
/**
 * Devuelve el numero con 2 digitos significativos
 * 
 * @param n
 *            Numero a convertir
 */
function n(n){
    return n > 9 ? n: "0" + n;
}

function mostrarMensaje(mensaje,options) {
	if(options.element) {
		options.element.addClass('alert-danger');
		options.element.attr({'title':mensaje});
	}
	tipo = options.type ? options.type : "error";
	noty({text: mensaje, type:tipo, layout:'top'});
}

/**
 * Obtiene un template para crear una fila de la tabla
 */
function __getRowTemplate() {
	var template = $.ajax({
			url:"/static/js/templates/row_reservarturno.template",
			async: false});
	return template.responseText;
}

function agregarFilaTurno(id, especialidad, especialista, dia, horario){
	var rowtemplate = __getRowTemplate();
	var table = $('#tabla_turnos > tbody:last');
	var row = rowtemplate.format(id, especialidad, especialista, dia, horario);
	table.append(row);
	
	$('.boton_eliminar#'+id).click(
			function(e){e.preventDefault();
			var id = parseInt(this.id);
			eliminar(id)
			$("#tr"+id).remove();
	});
}

// TODO Agrupar estas funciones en una clase Lista

/**
 * Obtiene la lista de turnos a reservar
 */
function getTurnos(){
	var json = $("#id_turnos").val();	// Reconstruyendo JSON
	return json ? eval(json) : new Array();
}

/**
 * Guarda la lista de turnos
 * 
 * @param turnos
 *            Lista de turnos a guardar
 */
function guardarTurnos(turnos) {
	var json = JSON.stringify(turnos);	// Creando JSON
	$("#id_turnos").val(json);
}

/**
 * Agrega un turno a la lista
 * 
 * @param turno_id
 *            id de turno a agregar
 */
function agregar(turno_id) {
	var turnos = getTurnos();
	if(turnos.indexOf(turno_id) == -1) {
		turnos.push(turno_id);
		guardarTurnos(turnos);
		var especialidad = $("#id_especialidad option:selected").text();
		var especialista = $("#id_especialista option:selected").text();
		var dia= $("#id_dia option:selected").text();
		var hora= $("#id_hora option:selected").text();
		agregarFilaTurno(turno_id,especialidad, especialista, dia, hora);
	} else {
		mostrarMensaje(MESSAGE_TURNO_YA_AGREGADO, 'danger');
	}
}

/**
 * Elimina un turno a la lista
 * 
 * @param turno_id
 *            id de turno a eliminar
 */
function eliminar(turno_id) {
	var turnos = getTurnos();
	var index = turnos.indexOf(turno_id);
	turnos.splice(index, 1);
	guardarTurnos(turnos);
}


$(document).ready(function(){
	$("#id_dni").blur(function() {
		var container = $("#id_dni");
		var dni = container.val();
		// TODO Validacion DNI
		if(dni) {
			url = '/json/afiliado/dni/{0}/'.format(dni);
			$.getJSON(url, function(data) {
				// TODO Caso DNI Inexistente
				if(data.length > 0) {
					// TODO Caso DNI Duplicado
					if (data.length > 1)
						console.log(MESSAGE_DNI_DUPLICADO);
					
					$("#id_afiliado").val(data[0].id);
					$("#id_numero").val(data[0].numero).mask('0000 0000 0000');
					$("#id_nombre").val(data[0].nombre);
					$("#id_apellido").val(data[0].apellido);
					
					// Verificar telefono
					url = '/json/afiliado/id/{0}/telefono/'.format(data[0].id);
					$.getJSON(url, function(data) {
						$("#id_telefono").val(data[0].telefono);
						$("#id_especialidad").focus();
					});
					// TODO Verificar presentismo
				} else {
					mostrarMensaje(MESSAGE_DNI_INEXISTENTE,{element:container});
				}
			});
		}
	});

	$("#id_especialidad").change(function() {
		$("#id_especialista, #id_dia, #id_hora").prop({disabled: true});
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
			}
		});
	});
	
	$("#id_especialista").change(function() {
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
			} else {
				mostrarMensaje(MESSAGE_NO_DIAS);
			}
		});
	});
	
	$("#id_dia").change(function() {
		$("#id_hora").prop({disabled: true});
		var milis = parseInt($("#id_dia").val());
		var id = $("#id_especialidad").val();
		if(!id)
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
	});
	
	$("#id_hora").change(function(e) {
		var destino = $('#id_agregar');
		destino.focus();
	});
	
	$("#id_agregar").click(function() {
		var turno_id = parseInt($("#id_hora").val());
		// TODO Validar
		if(turno_id) {
			agregar(turno_id);
			$(":submit").focus();
		}
	});
	
	$(':reset').click(function(){
		$('#tabla_turnos > tbody > tr').remove();
		$(':hidden').val('');
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
});
