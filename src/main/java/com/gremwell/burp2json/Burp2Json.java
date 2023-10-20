package com.gremwell.burppythonrequester;

import java.awt.Component;
import java.awt.datatransfer.StringSelection;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URLDecoder;
import java.net.http.HttpRequest;
import java.nio.charset.StandardCharsets;
import java.awt.Toolkit;
import java.awt.datatransfer.Clipboard;
import java.io.*;
import java.util.*;
import org.apache.commons.fileupload.MultipartStream;
import org.apache.commons.fileupload.MultipartStream.MalformedStreamException;
import org.apache.commons.fileupload.FileUploadBase.FileUploadIOException;
import javax.swing.JMenuItem;

import com.google.gson.Gson;

import burp.api.montoya.BurpExtension;
import burp.api.montoya.MontoyaApi;
import burp.api.montoya.core.ByteArray;
import burp.api.montoya.ui.contextmenu.*;
import burp.api.montoya.http.message.*;
import burp.api.montoya.http.message.requests.*;
import burp.api.montoya.http.message.params.*;
import burp.api.montoya.utilities.*;

public class Burp2Json implements ContextMenuItemsProvider​, BurpExtension {
	MontoyaApi api;

	@Override
	public void initialize(MontoyaApi api) {
		this.api = api;
		this.api.extension().setName("Burp2Python Requests");
		this.api.logging().logToOutput("Burp2Python extension has been loaded.");
		this.api.userInterface().registerContextMenuItemsProvider(this);
	}

	@Override
	public List<Component> provideMenuItems(AuditIssueContextMenuEvent event) {
		return null;
	}

	@Override
	public List<Component> provideMenuItems(WebSocketContextMenuEvent event) {
		return null;
	}

	@Override
	public List<Component> provideMenuItems(ContextMenuEvent event) {
		List<Component> items = new ArrayList<>();
		String menuItemName = "Burp2Python - no requests selected";
		/* Let's see if thre are any items selected in Target map */
		List<HttpRequestResponse> rrs = new ArrayList<HttpRequestResponse>();
		rrs.addAll(event.selectedRequestResponses());
		/* Let's see if there are any message editor requests responses selected */
		Optional<MessageEditorHttpRequestResponse> optionalRR = event.messageEditorRequestResponse();
		if (optionalRR.isPresent()) {
			api.logging().logToOutput("Event has optional MessageEditorRequestResponse");
			MessageEditorHttpRequestResponse mehrr = optionalRR.get();
			HttpRequestResponse rr = mehrr.requestResponse();
			rrs.add(rr);
			api.logging().logToOutput(rrs.size() + " request(s) selected");
		}
		if (rrs.size() > 0) {
			generateCode(rrs);
			menuItemName = "Burp2Python (" + rrs.size() + " request(s) selected) - generate";
		} else {
			api.logging().logToOutput("No requests/responses selected.");
		}
		items.add(new JMenuItem(menuItemName));

		this.api.logging().logToOutput("Burp2Python: " + rrs.size() + " requests selected.");
		return items;
	}

	private void generateCode(List<HttpRequestResponse> rrs) {
		Gson gson = new Gson();
		List<Map> requestList = new ArrayList<Map>();
		api.logging().logToOutput("Processing " + rrs.size() + " requests");
		String code = null;
		if (rrs.size() == 1) {
			try {
				code = gson.toJson(request2Map(rrs.get(0)));
			} catch (MalformedRequestException e) {
				api.logging().logToOutput("Got a malformed request, ignoring it.\n" + rrs.get(0).request().toString());
			} catch (URISyntaxException e) {
				api.logging().logToOutput(
						"Got a malformed URI, ignoring request.\n" + rrs.get(0).request().url().toString());
			} catch (IOException e) {
				api.logging().logToOutput("Something went wrong generating JSON, ignoring request.\n" + e.toString());
			}
		} else {
			for (HttpRequestResponse rr : rrs) {
				Map<String, String> requestMap = new LinkedHashMap<>();
				try {
					requestList.add(request2Map(rr));
				} catch (MalformedRequestException e) {
					api.logging()
							.logToOutput("Got a malformed request, ignoring it.\n" + rrs.get(0).request().toString());
				} catch (URISyntaxException e) {
					api.logging().logToOutput(
							"Got a malformed URI, ignoring request.\n" + rrs.get(0).request().url().toString());
				} catch (IOException e) {
					api.logging()
							.logToOutput("Something went wrong generating JSON, ignoring request.\n" + e.toString());
				}
			}
			code = gson.toJson(requestList);
		}
		if (code != null) {
			StringSelection stringSelection = new StringSelection(code);
			Clipboard clipboard = Toolkit.getDefaultToolkit().getSystemClipboard();
			clipboard.setContents(stringSelection, null);
		}
	}

	/*
	 * We are going to build an object that represents a request and can be used to
	 * replay it
	 * The structure is geared towards Python requests library, but should be
	 * sufficiently
	 * universal to be used with other languages and frameworks
	 * It looks like this:
	 * { "method" : "GET/PUT/POST/etc.", - HTTP request method
	 * "path" : "/blah", - request path, not including hostname, port or URL (query)
	 * parameters
	 * "comment" : "blah-blah", - Request comment, if entered in Burp. Can be used
	 * in script output
	 * "params" : {"name", "value"}, - URL query parameteres
	 * "data" : {"name":"value"}, - for application/x-www-form-urlencoded paramteres
	 * "data" : "string", - for other types of body data (i.e. XML for SOAP), except
	 * JSON and multipart/form-data
	 * "json" : "string", - JSON data in a string
	 * files : {"name":("filename", "content", "content type"), ...}
	 * "headers" : {"name" : "value"} - request headers. Content-type header is
	 * added based on the original request
	 * }
	 * Other headers are ignored.
	 * If there is nothing to put in "data", "json" or "params", they keys will not
	 * be present
	 * If the request has an empty body, but does have Content-Type header, "data"
	 * will be set to empty string "",
	 * or empty object {} depending on content type.
	 * }
	 */
	private Map<String, Object> request2Map(burp.api.montoya.http.message.HttpRequestResponse reqResp)
			throws MalformedRequestException, URISyntaxException, IOException, FileUploadIOException,
			MalformedStreamException {
		Map<String, Object> requestMap = new LinkedHashMap<>();
		burp.api.montoya.http.message.requests.HttpRequest req = reqResp.request();
		requestMap.put("method", req.method());
		/*
		 * Not using req.path() here because it includes URL paramteres, and we don't
		 * want that,
		 * do we user req.url() and extract path from it using Java URI class
		 */
		URI uri = new URI(req.url());
		requestMap.put("path", uri.getPath());
		if (reqResp.annotations().notes() != null) {
			requestMap.put("comment", reqResp.annotations().notes());
		} else {
			requestMap.put("comment", "");
		}

		Map<String, String> requestHeaders = new LinkedHashMap<>();
		/* Slightly different processing depending on Content-Type */
		if (req.contentType() == ContentType.URL_ENCODED) {
			/* Create a request body with parameters */
			Map<String, String> body_params = new LinkedHashMap<>();
			for (ParsedHttpParameter param : req.parameters()) {
				if (param.type() == HttpParameterType.BODY) {
					body_params.put(param.name(), api.utilities().urlUtils().decode(param.value()));
				}
			}
			api.logging().logToOutput("Detected URL-encoded body");
			requestMap.put("data", body_params);
		} else if (req.contentType() == ContentType.XML) {
			/* This could be SOAP, let's look for SOAP-specific headers */
			for (HttpHeader header : req.headers()) {
				if (header.name().toLowerCase().equals("soapaction")) { /* Aha! */
					requestHeaders.put(header.name(), header.value());
				}
			}
			api.logging().logToOutput("Detected XML body");
			requestMap.put("data", req.bodyToString()); /* Dump body as is */
		} else if (req.contentType() == ContentType.JSON) {
			api.logging().logToOutput("Detected JSON body");
			requestMap.put("json", req.bodyToString());
		} else if (req.contentType() == ContentType.MULTIPART) {
			api.logging().logToOutput("Detected multipart body");
			/*
			 * Montoya APi does not have proper support for parsing multipart bodies,
			 * so we are using Apache Commons classes to do the job
			 */

			ByteArrayInputStream content = new ByteArrayInputStream(req.body().getBytes());
			String content_type = req.headerValue("Content-type");
			api.logging().logToOutput("Content-type: " + content_type);
			String boundary = content_type.substring(content_type.indexOf("boundary=") + "boundary=".length());
			api.logging().logToOutput("boundary: " + boundary);
			@SuppressWarnings("deprecation")
			MultipartStream multipartStream = new MultipartStream(content, boundary.getBytes());

			boolean nextPart = multipartStream.skipPreamble();
			api.logging().logToOutput("skipPreamble() returned " + nextPart);
			HashMap<String, Object> file_params  = new LinkedHashMap<>();
			while (nextPart) {
				List<Object> file_param = new LinkedList<>();
				/* The format of this parameter is as follows:
				 * ["file_name", "file_content", "file_content_type"]
				 * For example:
				 * ["image.png", "data here", "image/png"]
				 * This is not going to work well with large binary data
				 */
				String headers = multipartStream.readHeaders();
				api.logging().logToOutput("Headers: " + headers);
				String[] hh = headers.split("\r\n");
				String file_content_type = null, file_param_name = null, file_param_filename = null;
				for (String h : hh) {
					String header_name, header_value;
					String[] tuple = h.split(": ");
					header_name = tuple[0];
					header_value = tuple[1];
					if(header_name.toLowerCase().equals("content-disposition")) {
						String[] fields = header_value.split("; ");
						/* We expect something like this:
						 * form-data; name="file"; filename="test.csv"
						 */
						for (String f : fields) {
							if(f.contains("=")) {
								String[] name_value = f.split("=");
								if(name_value[0].equals("name")) {
									file_param_name = name_value[1].replaceAll("^\"|\"$", ""); // remove leading and training quotes if any
								} else if(name_value[0].equals("filename")) {
									file_param_filename = name_value[1].replaceAll("^\"|\"$", "");
								}
							}
						}
					} else if (header_name.toLowerCase().equals("content-type")) {
						file_content_type = header_value;
					}
 				}
				ByteArrayOutputStream out = new ByteArrayOutputStream();
				multipartStream.readBodyData(out);
				byte[] part_content = out.toByteArray();
				api.logging().logToOutput("Body: " + part_content.length + " bytes");

				if(file_param_filename != null) {
					file_param.add(file_param_filename);
				} else {
					file_param.add("");
				};
				if(part_content != null) {
					String c = new String(part_content, StandardCharsets.UTF_8);
					file_param.add(c);
				} else {
					file_param.add("");
				};
				if(file_content_type != null) {
					file_param.add(file_content_type);
				};
				file_params.put(file_param_name, file_param);
				nextPart = multipartStream.readBoundary();
			
			}
			requestMap.put("files", file_params);

		} else { /* handling for all other content types */
			api.logging().logToOutput("Cannot determine body type, using as is");
			if (req.body() != null) {
				requestMap.put("data", req.bodyToString());
			}
		}
		/* Handle query params if any */
		Map<String, String> query_params = new LinkedHashMap<>();
		for (ParsedHttpParameter param : req.parameters()) {
			if (param.type() == HttpParameterType.URL) {
				query_params.put(param.name(), api.utilities().urlUtils().decode(param.value()));
			}
		}
		requestMap.put("params", query_params);
		 // Preserve original Content-type, except for multipart requests
		 // For multipart requests let the user set content type automatically
		 // with correct boundary
		if(req.contentType() != ContentType.MULTIPART) {
			requestHeaders.put("Content-type", getRequestContentType(req));
		}
		requestMap.put("headers", requestHeaders);
		return requestMap;
	}

	private String getRequestContentType(burp.api.montoya.http.message.requests.HttpRequest req) {
		for (HttpHeader header : req.headers()) {
			if (header.name().toLowerCase().equals("content-type")) {
				return header.value();

			}
		}
		return null;
	}

}