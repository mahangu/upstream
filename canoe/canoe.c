/*	Author: Ryan Zeigler, 2006
	This file is part of Upstream the log submission system.
	This file is released under the GPL
*/

#include <gtk/gtk.h>
#include <stdlib.h>
#include <string.h>

#define NETWORK_FLAG "-n"
#define STANDARD_FLAG "-s"
#define VIDEO_FLAG "-v"

/* Functions necessary for fetching the support composite.  Support composite
returns -1 if user cancels */
gint get_support_composite();
GtkWidget* create_support_type_dialog(int num_elems, GtkWidget** listing);

/* Functions necessary to get the program name */
gchar* get_program_name(const gchar* input);

/* Functions necessary for fetching the e-mail address. Returns NULL if
user cancels, and "" if emptry string is entered */
gchar* get_email_address();
GtkWidget* create_email_dialog(GtkWidget** email_entry);

/* Functions necessary for fetching the support message. Same as for get_email_address() */
gchar* get_support_message();
GtkWidget* create_support_request_dialog();

/* Management of the vector that the program should be executed with */
gchar** generate_argv_vector(const gchar* prog_name, const gchar* email_addr, const char* support_msg, const gint support_type);
void free_argv_vector(gchar** argv_vect);

void handle_upstream_async_execution(GPid pid, gint stdin_fd, gint stdout_fd, gint stderr_fd);


/* Enumeration allowing all of the SupportModes to be specified */
enum SupportModes { standard = 1 << 0, network = 1 << 1, video = 1 << 2, sound = 1 << 3 };

struct _ThreadParam
{
	GtkTextBuffer* buffer;
	GtkWidget* button;
};

typedef struct _ThreadParam ThreadParam;



int main(int argc, char* argv[])
{
	
	gint loop_control;
	
	gchar* prog_path;
	gchar* prog_name;
	gchar* email_addr;
	gchar* support_msg;
	gint support_composite = 0;
	
	gchar** argv_vector;
	
	char* results_tmp_buffer;
	
	GPid invocation_pid;
	gint stdin_fd;
	gint stdout_fd;
	gint stderr_fd;
	GError* invocation_error = NULL;

	GtkWidget* error_dialog;
	GtkWidget* error_label;

	/* Temporary variables for sychnronous testing 
	gchar* stdout_tmp;
	gchar* stderr_tmp;
	gint exit_status;
	GError* sync_error = NULL;
	*/
	
	/* Allow forking if gtk can't be enabled for some reason */
	if(!gtk_init_check(&argc, &argv))
	{
		g_print("Could not initialize GTK/X\n");
		g_print("This is a placeholder for switching to alternate mode of input\n");
	}else
	{
		/* Print a help message */
		if(argc == 2 && !strcmp(argv[1], "-h"))
		{
			g_print("Usage: canoe /path/to/upstream.py\nDo not include upstream.py in the actual string\n");
			return 0;
		}
		
		/* Deal with paths and the like */
		if(argc == 2)
		{
			prog_name = get_program_name(argv[1]);
			prog_path = g_strdup(argv[1]);	
		}else
		{
			/* In future this might change to a default location, possibly /var/lib/ or some such */
			g_print("A path to program is required\n");
			return 0;
		}

		/* Get the users input email address */
		email_addr  = get_email_address();
		if(email_addr == NULL)
		{
			return 0;
		}
		
		/* Get the users input support message */
		support_msg = get_support_message();
		if(support_msg == NULL)
		{
			return 0;
		}
		
		/* Get an int containing the flags that represent the suppport category */
		support_composite = get_support_composite();
		if(support_composite == -1)
		{
			return 0;
		}
		
		/* Generate the argument vector to be set to the program */
		argv_vector = generate_argv_vector(prog_name, email_addr, support_msg, support_composite);
		for(loop_control = 0; argv_vector[loop_control] != NULL; loop_control++)
		{
			g_print("%s ", argv_vector[loop_control]);
		}
		g_print("\n");
		g_free(prog_name);
		g_free(email_addr);
		g_free(support_msg);
		/* Execute the program in an asynchronous manner */
		
		if(!g_spawn_async_with_pipes(prog_path, argv_vector, NULL, G_SPAWN_SEARCH_PATH, NULL, NULL, &invocation_pid, &stdin_fd, &stdout_fd, &stderr_fd, &invocation_error))
		{
			results_tmp_buffer = g_strconcat("Unable to spawn child process.\nThis is a bug in the program.\nThe resulting error was:\n", invocation_error->message, "\n", NULL);
			error_dialog = gtk_dialog_new_with_buttons("Error!", NULL,  GTK_DIALOG_MODAL, GTK_STOCK_OK, GTK_RESPONSE_ACCEPT, NULL);
			error_label = gtk_label_new(results_tmp_buffer);
			gtk_widget_show(error_label);
			g_free(results_tmp_buffer);
			gtk_box_pack_start(GTK_BOX(GTK_DIALOG(error_dialog)->vbox), error_label, TRUE, FALSE, 5);
			gtk_dialog_run(GTK_DIALOG(error_dialog));
			gtk_widget_destroy(error_dialog);			
		
		}else
		{
			/* Program execution was successful */
			handle_upstream_async_execution(invocation_pid, stdin_fd, stdout_fd, stderr_fd);
		}
		g_print("Finished running command\n");
		/*
		if(!g_spawn_sync(prog_path, argv_vector, NULL, G_SPAWN_SEARCH_PATH, NULL, NULL, &stdout_tmp, &stderr_tmp, &exit_status, &sync_error))
		{
			g_print("Unable to spawn upstream.py process\n");
			g_print("Returned error was: %s\n", sync_error->message);
		}else
		{
			g_print("Standard out:\n%s\n", stdout_tmp);
			g_print("Standard error:\n%s\n", stderr_tmp);
			g_print("Exit status: %d\n", exit_status);
		}*/
		g_spawn_close_pid(invocation_pid);
		g_error_free(invocation_error);
		g_free(prog_path);
		free_argv_vector(argv_vector);
	}
	return 0;
}

/* Note that after this function is invoked, email_msg and others may be free'd as this element "takes possession of the data"
The returned vector should later be free'd by free argv_vector */

/* Setup the argv vector used for invoking upstream.py */
gchar** generate_argv_vector(const gchar* prog_name, const gchar* email_addr, const char* support_msg, const gint support_type )
{
	gchar** argv_store;
	gint argv_access = 0;
	gint num_argv = 3;

	/* Parenthesis required due to order of operations or something wierd like that */
	if((support_type & standard) == standard)
	{
		num_argv++;
	}
	if((support_type & network) == network)
	{
		num_argv++;
	}
	if((support_type & video) == video)
	{
		num_argv++;
	}
	argv_store = g_malloc((num_argv * sizeof(gchar*)) + 1);
	
	argv_store[argv_access++] = g_strdup(prog_name);
	argv_store[argv_access++] = g_strdup(email_addr);
	argv_store[argv_access++] = g_strdup(support_msg);
	
	if((support_type & standard) == standard)
	{
		argv_store[argv_access++] = g_strdup(STANDARD_FLAG);
	}
	if((support_type & network) == network)
	{
		argv_store[argv_access++] = g_strdup(NETWORK_FLAG);
	}
	if((support_type & video) == video)
	{
		argv_store[argv_access++] = g_strdup(VIDEO_FLAG);
	}
	/* Finish off the vector with a NULL */
	argv_store[argv_access++] = NULL;
	return argv_store;
}

void free_argv_vector(gchar** argv_vect)
{
	gint argv_access = 0;
	while(argv_vect[argv_access] != NULL)
	{
		g_free(argv_vect[argv_access++]);
	}
	g_free(argv_vect);
}

gchar* get_program_name(const gchar* input)
{
	gchar* prog_name;
	if(input[strlen(input) - 1] == '/')
	{
		prog_name = g_strconcat(input, "upstream.py", NULL);
	}else
	{
		prog_name = g_strconcat(input, "/upstream.py", NULL);
	}
	return prog_name;
}

gchar* get_email_address()
{
	GtkWidget* email_dialog;
	GtkWidget* email_entry;
	gchar* email_addr;
	gint response_code;
	
	email_dialog = create_email_dialog(&email_entry);
	response_code = gtk_dialog_run(GTK_DIALOG(email_dialog));
	
	gtk_widget_hide(email_dialog);
	
	if(response_code == GTK_RESPONSE_NONE || response_code == GTK_RESPONSE_CANCEL)
	{
		return NULL;
	}else
	{
		email_addr = g_strdup(gtk_entry_get_text(GTK_ENTRY(email_entry)));
		gtk_widget_destroy(email_dialog);
		return email_addr;
	}			
}

GtkWidget* create_email_dialog(GtkWidget** email_entry)
{
	
	GtkWidget* dialog;
	GtkWidget* email_label;
	
	dialog = gtk_dialog_new_with_buttons("E-mail", NULL, GTK_DIALOG_MODAL, GTK_STOCK_CANCEL, GTK_RESPONSE_CANCEL, GTK_STOCK_OK, GTK_RESPONSE_OK, NULL);
	gtk_window_set_default_size(GTK_WINDOW(dialog), 400, -1);
	email_label = gtk_label_new("Enter your e-mail address.");
	*email_entry = gtk_entry_new();
	
	gtk_widget_show(email_label);
	gtk_widget_show(*email_entry);
	
	gtk_box_pack_start(GTK_BOX(GTK_DIALOG(dialog)->vbox), email_label, TRUE, TRUE, 5);
	gtk_box_pack_start(GTK_BOX(GTK_DIALOG(dialog)->vbox), *email_entry, TRUE, TRUE, 5);
	
	return dialog;
}

gchar* get_support_message()
{
	GtkWidget* support_dialog;
	GtkWidget* support_request_multiline;
	GtkTextBuffer* support_request_buffer;
	GtkTextIter start, end;
	gchar* support_msg;
	gchar* support_msg_final;
	gint response_code;
	
	support_dialog = create_support_request_dialog(&support_request_multiline);
	response_code = gtk_dialog_run(GTK_DIALOG(support_dialog));
	gtk_widget_hide(support_dialog);
	
	if(response_code == GTK_RESPONSE_NONE || response_code == GTK_RESPONSE_CANCEL)
	{
		return NULL;
	}else
	{
		support_request_buffer = gtk_text_view_get_buffer(GTK_TEXT_VIEW(support_request_multiline));
		gtk_text_buffer_get_iter_at_offset(support_request_buffer, &start, 0);
		gtk_text_buffer_get_iter_at_offset(support_request_buffer, &end, -1);
		/* This does not need to be strdup'ed because buffer_get_text() returns an allocated string */
		support_msg = gtk_text_buffer_get_text(support_request_buffer, &start, &end, TRUE);
		support_msg_final = g_strconcat("\"", support_msg, "\"", NULL);
		gtk_widget_destroy(support_dialog);
		g_free(support_msg);
		return support_msg_final;
	}
}

GtkWidget* create_support_request_dialog(GtkWidget** multiline)
{
	
	GtkWidget* dialog;
	GtkWidget* support_request_label;
	
	dialog = gtk_dialog_new_with_buttons("Support message", NULL, GTK_DIALOG_MODAL, GTK_STOCK_CANCEL, GTK_RESPONSE_CANCEL, GTK_STOCK_OK, GTK_RESPONSE_OK, NULL);
	gtk_window_set_default_size(GTK_WINDOW(dialog),  400, 200);
	support_request_label = gtk_label_new("Enter your support request.");
	*multiline = gtk_text_view_new();
	
	gtk_widget_show(support_request_label);
	gtk_widget_show(*multiline);
	
	gtk_box_pack_start(GTK_BOX(GTK_DIALOG(dialog)->vbox), support_request_label, FALSE, FALSE, 5);
	gtk_box_pack_start(GTK_BOX(GTK_DIALOG(dialog)->vbox), *multiline, TRUE, TRUE, 5);
	
	return dialog;
}

gint get_support_composite()
{
	GtkWidget* type_dialog;

	GtkWidget* network_toggle;
	GtkWidget* sound_toggle;
	GtkWidget* video_toggle;
	GtkWidget* tracker[3];

	gint response_code;
	gint composite = 0;
	
	tracker[0] = network_toggle = gtk_check_button_new_with_label("Networking");
	tracker[1] = sound_toggle = gtk_check_button_new_with_label("Sound");
	tracker[2] = video_toggle = gtk_check_button_new_with_label("Video/Display");
	
	type_dialog = create_support_type_dialog(3, tracker);
	response_code = gtk_dialog_run(GTK_DIALOG(type_dialog));
	gtk_widget_hide(type_dialog);
	if(response_code == GTK_RESPONSE_NONE || response_code == GTK_RESPONSE_CANCEL)
	{
		g_print("User aborted\n");
		return -1;
	}else
	{		
		if(gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(network_toggle)))
		{
			composite = (composite | network);
		}
		if(gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(sound_toggle)))
		{
			composite = (composite | sound);
		}
		if(gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(video_toggle)))
		{
			composite = (composite | video);
		}
		/* Always send standard */
		composite = (composite | standard);
		gtk_widget_destroy(type_dialog);
		return composite;
	}
}

GtkWidget* create_support_type_dialog(int num_elems, GtkWidget** listing)
{
	GtkWidget* dialog;
	GtkWidget* support_type_label;
	gint loop_control;
	dialog = gtk_dialog_new_with_buttons("Support categories", NULL, GTK_DIALOG_MODAL, GTK_STOCK_CANCEL, GTK_RESPONSE_CANCEL, GTK_STOCK_OK, GTK_RESPONSE_OK, NULL);
	gtk_window_set_default_size(GTK_WINDOW(dialog), 400, -1);
	support_type_label = gtk_label_new("Mark all items that pertain to your issues.");
	gtk_widget_show(support_type_label);
	gtk_box_pack_start(GTK_BOX(GTK_DIALOG(dialog)->vbox), support_type_label, TRUE, FALSE, 5);
	for(loop_control = 0; loop_control < num_elems; loop_control++)
	{
		gtk_widget_show(listing[loop_control]);
		gtk_box_pack_start(GTK_BOX(GTK_DIALOG(dialog)->vbox), listing[loop_control], TRUE, FALSE, 5);
	}	
	return dialog;
}

/* This function blocks in GTK main until close is executed */
void handle_upstream_async_execution(GPid pid, gint stdin_fd, gint stdout_fd, gint stderr_fd)
{
	GtkWidget* window;
	GtkWindow* hbox;
	GtkWidget* label;
	GtkWidget* text_view;
	
	GtkTextBuffer* text_view_buffer;
	
	ThreadParam param;
	
	window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
	gtk_window_set_default_size(GTK_WINDOW(window), 400, 400);
	gtk_window_set_resizable(GTK_WINDOW(window), FALSE);
}
