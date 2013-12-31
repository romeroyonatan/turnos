DEFAULT_MESSAGE = "Seleccionar";
MESSAGE_NO_DIAS = "El especialista no posee días disponibles para reservar turnos";
MESSAGE_NO_TURNOS = "No hay turnos disponibles este día";
MESSAGE_TURNO_YA_AGREGADO = "Ya agregó este turno";
MESSAGE_DNI_DUPLICADO_TITLE = "DNI duplicado";
MESSAGE_DNI_DUPLICADO_DESCRIPCION = "Deberá ingresar el número de afiliado para realizar la reserva";
MESSAGE_DNI_INEXISTENTE_TITLE = "DNI Inexistente";
MESSAGE_DNI_INEXISTENTE_DESCRIPCION = "Verifique que el número de DNI ingresado sea correcto";
MESSAGE_NUMERO_DUPLICADO = "Número de afiliado duplicado";
MESSAGE_NUMERO_INEXISTENTE_TITLE = "Número de afiliado Inexistente";
MESSAGE_NUMERO_INEXISTENTE_DESCRIPCION = "Verifique que el número de número de afiliado ingresado sea correcto";
MESSAGE_PRESENTISMO = "El afiliado ha faltado a muchos turnos en los ultimos meses";
DIA=["Domingo", "Lunes", "Martes", "Miercoles", "Jueves","Viernes","Sabado"];
MES=["enero", "febrero","marzo", "abril","mayo", "junio","julio","agosto","septiembre","octubre","noviembre","diciembre"];	
ESTADOS={C:"Completo",S:"Sobreturno"};

/**
 * Permite formatear una cadena como en C# mediante ubicadores posicionales
 * {0}{1}
 */
String.prototype.format = function () {
    var literal = this;
    if(arguments[0] instanceof Object) {
    	var object = arguments[0];
    	for (var i in object) {
	        var regex = new RegExp('\\{' + i + '\\}', 'g');
	        literal = literal.replace(regex, object[i]);
	    }
    } else {
	    for (var i = 0; i < arguments.length; i++) {
	        var regex = new RegExp('\\{' + i + '\\}', 'g');
	        literal = literal.replace(regex, arguments[i]);
	    }
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
	if(options && options.element) {
		options.element.addClass('error');
		options.element.attr({'title':mensaje});
	}
	title = options && options.title ? options.title : "";
	template = "<div><h1>{0}</h1><p>{1}</p></div>";
	text = template.format(title, mensaje);
	tipo = options && options.type ? options.type : "error";
	noty({text: text, type:tipo, layout:'bottom'});
}

function agregarFilaTurno(id, especialidad, especialista, dia, horario){
	var rowtemplate = __getRowTemplate();
	var container = $('#list-container');
	var row = rowtemplate.format(id, especialidad, especialista, dia, horario);
	container.append(row);
	
	$('.boton_eliminar#'+id).click(
			function(e){e.preventDefault();
			var id = parseInt(this.id);
			eliminar(id)
			$("#tr"+id).remove();
	});
}

function Lista(contenedor, options) {
	/** Este atributo hace referencia a un objecto del DOM que almacenará los
	 * ID de los objetos seleccionados */
	this.container = contenedor;
	this.listContainer = options && options.listContainer ? 
						 options.listContainer : 
					     $('#list-container');
	this.template = options && options.template ? this.__getTemplate();
	this.load();
}
/**
 * Obtiene la lista de objetos
 */
Lista.prototype.load = function(){
	var json = this.container.val(); // Reconstruyendo JSON
	this.objects = json ? eval(json) : new Array();
	return this.objects;
}

/**
 * Obtiene un template para crear una fila de la tabla
 */
Lista.prototype.__getTemplate = function() {
	var template = $.ajax({
			url:"/static/js/templates/generic.template.html",
			async: false});
	return template.responseText;
}

/**
 * Guarda la lista de objetos
 * 
 * @param turnos
 *            Lista de turnos a guardar
 */
Lista.prototype.save = function (){
	var json = JSON.stringify(this.objects);// Creando JSON
	this.container.val(json);
}

/**
 * Agrega un objeto a la lista
 */
Lista.prototype.add = function(obj) {
	if(this.objects.indexOf(obj.id) == -1) {
		this.objects.push(obj.id);
		this.save();
		this.addDOM(obj);
	} else {
		return false;
	}
}

/**
 * Agrega un elemento al DOM
 */
Lista.prototype.addDOM = function(obj) {
	t = this.template.format(obj)
	this.listContainer.append(t);
}

/**
 * Elimina un elemento de la lista
 * 
 * @param id
 *            id del objeto a eliminar
 */
Lista.prototype.remove = function (id) {
	var index = this.objects.indexOf(id);
	this.objects.splice(index, 1);
	this.save();
}

function Afiliado(obj) {
	this.id = obj.id;
	this.dni = obj.dni;
	this.numero = obj.numero;
	this.nombre = obj.nombre;
	this.apellido = obj.apellido;
	this.obtenerTelefono();
	this.verificarPresentismo();
}

/**
 * Obtiene el telefono del afiliado
 * @param afiliado
 *            id del afiliado
 */
Afiliado.prototype.obtenerTelefono = function () {
	url = '/json/afiliado/id/{0}/telefono/'.format(this.id);
	$.getJSON(url, function(data) {
		if(data) {
			this.telefono = data[0].telefono;
			$("#id_especialidad").focus();
		} else {
			$("#id_telefono").focus();
		}
	});
}

Afiliado.prototype.verificarPresentismo = function () {
	url = '/json/presentismo/{0}/'.format(this.id);
	$.getJSON(url, function(data) {
		this.presentismo = data.presentismo_ok;
	});
}

Afiliado.prototype.mostrar = function () {
	$("#id_afiliado").val(this.id);
	$("#id_dni").val(this.dni);
	$("#id_numero").val(this.numero).mask('0000 0000 0000');
	$("#id_nombre").val(this.nombre);
	$("#id_apellido").val(this.apellido);
	$("#id_telefono").val(this.telefono);
	if(!this.presentismo)
		mostrarMensaje(MESSAGE_PRESENTISMO, {type:'information'});
}

$(document).ready(function(){
	var ajax = $.ajax({
		url:"/static/js/templates/reservarturno.template.html",
		async: false});
	l = new Lista($('#id_turnos'),{template=ajax.responseText});

	$("#id_dni").blur(function() {
		var container = $("#id_dni");
		var dni = container.val();
		if(/\d+/.test(dni)) {
			url = '/json/afiliado/dni/{0}/'.format(dni);
			$.getJSON(url, function(data) {
				if (data.length == 1) {
					var a = new Afiliado(data[0]);
					a.mostrar();
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
					var a = new Afiliado(data[0]);
					a.mostrar();
				} else if (data.length > 1){
					mostrarMensaje(MESSAGE_NUMERO_DUPLICADO,{type:'warning'});
				} else {
					mostrarMensaje(MESSAGE_NUMERO_INEXISTENTE_DESCRIPCION,
							{title:MESSAGE_NUMERO_INEXISTENTE_TITLE, element:container});
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
	});
	
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
			l.add(turno);
			$(":submit").focus();
		} else {
			mostrarMensaje("Debe seleccionar un horario de un turno disponible",
							{element:$('#id_hora')});
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
