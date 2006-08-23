/*	Author: Ryan Zeigler, 2006
	This file is part of Upstream the log submission system.
	This file is released under the GPL
*/

#include <gtk/gtk.h>
#include <stdlib.h>
#include <string.h>

GtkWidget* create_email_dialog();
GtkWidget* create_support_request_dialog();
GtkWidget* create_support_type_dialog();

enum SupportModes { standard = 1 << 0, network = 1 << 1, video = 1 << 2, sound = 1 << 3 };
gchar** generate_command_flags(gint* num_flags);

GtkWidget* email_label;
GtkWidget* email_entry;

GtkWidget* support_request_label;
GtkWidget* support_request_box;

GtkWidget* support_type_label;
GtkWidget* network_toggle;
GtkWidget* sound_toggle;
GtkWidget* video_toggle;

int main(int argc, char* argv[])
{
	
	GtkWidget* email_dialog;
	GtkWidget* support_dialog;
	GtkWidget* type_dialog;
	gint response_code;
	gint num_cmd_flags;
	
	/* Temporary variables necessary for upstream.py invocation */
	GtkTextBuffer* support_request_buffer;
	GtkTextIter start, end;
	gint support_composite;
	gchar* prog_path;
	gchar* prog_name;
	gchar* email_addr;
	gchar* support_msg;
	gchar* support_msg_final;
	/* Used for invoking child process */
	gchar** execute_argv;
	gint num_argv = 3;
	gint execute_argv_access;
	gint stdin_fd;
	GIOChannel* stdin_pipe;
	gint stdout_fd;
	GIOChannel* stdout_pipe;
	gint stderr_fd;
	GIOChannel* stderr_pipe;
	gint child_pid;
	GError* execute_error = NULL;
	/* Used for getting returned data from the file */
	GError* read_error = NULL;
	GError* stderr_error = NULL;
	gchar* read_data;
	gchar* read_stderr;
	gint exit_status;
	gsize read_length;
	gsize read_terminate_pos;
	gint loop_control;
	
	if(!gtk_init_check(&argc, &argv))
	{
		g_print("Could not initialize GTK/X\n");
		g_print("This is a placeholder for switching to alternate mode of input\n");
	}

	if(argc == 2 && !strcmp(argv[1], "-h"))
	{
		g_print("Usage: canoe /path/to/upstream.py\nDo not include upstream.py in the actual string\n");
		return 0;
	}
	
	if(argc == 2)
	{
		if(argv[1][strlen(argv[1]) - 1] == '/')
		{
			prog_name = g_strconcat(argv[1], "upstream.py", NULL);
		}else
		{
			prog_name = g_strconcat(argv[1], "/upstream.py", NULL);
		}
		prog_path = g_strdup(argv[1]);
	}else
	{
		g_print("A path to program is required");
		return 0;
	}

	email_dialog = create_email_dialog();
	response_code = gtk_dialog_run(GTK_DIALOG(email_dialog));
	gtk_widget_hide(email_dialog);
	if(response_code == GTK_RESPONSE_NONE || response_code == GTK_RESPONSE_CANCEL)
	{
		g_print("User aborted\n");
		return 0;
	}else
	{
		email_addr = g_strdup(gtk_entry_get_text(GTK_ENTRY(email_entry)));
		gtk_widget_destroy(email_dialog);
	}		
	
	support_dialog = create_support_request_dialog();
	response_code = gtk_dialog_run(GTK_DIALOG(support_dialog));
	gtk_widget_hide(support_dialog);
	if(response_code == GTK_RESPONSE_NONE || response_code == GTK_RESPONSE_CANCEL)
	{
		g_print("User aborted\n");
		return 0;
	}else
	{
		support_request_buffer = gtk_text_view_get_buffer(GTK_TEXT_VIEW(support_request_box));
		gtk_text_buffer_get_iter_at_offset(support_request_buffer, &start, 0);
		gtk_text_buffer_get_iter_at_offset(support_request_buffer, &end, -1);
		/* This does not need to be strdup'ed because buffer_get_text() returns an allocated string */
		support_msg = gtk_text_buffer_get_text(support_request_buffer, &start, &end, TRUE);
		support_msg_final = g_strconcat("\"", support_msg, "\"", NULL);
		g_free(support_msg);
		gtk_widget_destroy(support_dialog);
	}
		
	
	type_dialog = create_support_type_dialog();
	response_code = gtk_dialog_run(GTK_DIALOG(type_dialog));
	gtk_widget_hide(type_dialog);
	if(response_code == GTK_RESPONSE_NONE || response_code == GTK_RESPONSE_CANCEL)
	{
		g_print("User aborted\n");
		return 0;
	}else
	{		
		support_composite = get_support_type_composite();
		gtk_widget_destroy(type_dialog);
	}
	
	/* Setup parameters for invoking upstream.py */
	
	if(support_composite & standard == standard)
	{
		num_argv++;
	}
	if(support_composite & network == network)
	{
		num_argv++;
	}
	if(support_composite & sound == sound)
	{
		num_argv++;
	}
	if(support_composite & video == video)
	{
		num_argv++;
	}
	/* The + 1 add support for the terminating NULL */
	execute_argv  = g_malloc((num_argv * sizeof(char*)) + 1);
	if(execute_argv == NULL)
	{
		g_print("Out of memory - aborting\n");
		exit(1);
	}

	execute_argv_access = 0;
	execute_argv[execute_argv_access++] = prog_name;
	execute_argv[execute_argv_access++] = email_addr;
	execute_argv[execute_argv_access++] = support_msg_final;

	if((support_composite & network) == network)
	{
		execute_argv[execute_argv_access++] = "-n";
	}
	if((support_composite & standard) == standard)
	{
		execute_argv[execute_argv_access++] = "-s" ;
	}
	execute_argv[execute_argv_access++] = NULL;
	
	/*	
	if(!g_spawn_async_with_pipes(NULL, execute_argv,  NULL, G_SPAWN_SEARCH_PATH | G_SPAWN_DO_NOT_REAP_CHILD, NULL, NULL, &child_pid, &stdin_fd, &stdout_fd, &stderr_fd, &execute_error))
	{
		
		g_print("Execution failed\n");
		return 0;
	}
		
	stdin_pipe = g_io_channel_unix_new(stdin_fd);
	stdout_pipe = g_io_channel_unix_new(stdout_fd);
	stderr_pipe = g_io_channel_unix_new(stderr_fd);
	
	
	g_print("Now dumping output from program\n");
	if(g_io_channel_read_to_end(stdout_pipe, &read_data, &read_length, &read_error) != G_IO_STATUS_NORMAL)
	{
		g_print("Failure");
	}*/
	for(loop_control = 0; loop_control < execute_argv_access; loop_control++)
	{
		g_print("%s ", execute_argv[loop_control]);
	}
	
	if(!g_spawn_sync(prog_path, execute_argv, NULL, G_SPAWN_SEARCH_PATH, NULL, NULL,  &read_data, &read_stderr, &exit_status, &execute_error))
	{
		g_print("Failure");
		return 0;
	}
	
	g_print("Output: %s\n", read_data);
	g_print("StdErr: %s\n", read_stderr);
	
	
	g_free(execute_argv);
	g_free(support_msg_final);
	g_free(email_addr);
	g_free(prog_name);
	g_free(prog_path);

	return 0;
}

GtkWidget* create_email_dialog()
{
	
	GtkWidget* dialog;

	dialog = gtk_dialog_new_with_buttons("E-mail", NULL, GTK_DIALOG_MODAL, GTK_STOCK_CANCEL, GTK_RESPONSE_CANCEL, GTK_STOCK_OK, GTK_RESPONSE_OK, NULL);
	gtk_window_set_default_size(GTK_WINDOW(dialog), 400, -1);
	email_label = gtk_label_new("Enter your e-mail address.");
	email_entry = gtk_entry_new();
	
	gtk_widget_show(email_label);
	gtk_widget_show(email_entry);
	
	gtk_box_pack_start(GTK_BOX(GTK_DIALOG(dialog)->vbox), email_label, TRUE, TRUE, 5);
	gtk_box_pack_start(GTK_BOX(GTK_DIALOG(dialog)->vbox), email_entry, TRUE, TRUE, 5);
	
	return dialog;
}

GtkWidget* create_support_request_dialog()
{
	
	GtkWidget* dialog;

	dialog = gtk_dialog_new_with_buttons("E-mail", NULL, GTK_DIALOG_MODAL, GTK_STOCK_CANCEL, GTK_RESPONSE_CANCEL, GTK_STOCK_OK, GTK_RESPONSE_OK, NULL);
	gtk_window_set_default_size(GTK_WINDOW(dialog),  400, 200);
	support_request_label = gtk_label_new("Enter your support request.");
	support_request_box = gtk_text_view_new();
	
	gtk_widget_show(support_request_label);
	gtk_widget_show(support_request_box);
	
	gtk_box_pack_start(GTK_BOX(GTK_DIALOG(dialog)->vbox), support_request_label, FALSE, FALSE, 5);
	gtk_box_pack_start(GTK_BOX(GTK_DIALOG(dialog)->vbox), support_request_box, TRUE, TRUE, 5);
	
	return dialog;
}

GtkWidget* create_support_type_dialog()
{
	GtkWidget* dialog;
	dialog = gtk_dialog_new_with_buttons("E-mail", NULL, GTK_DIALOG_MODAL, GTK_STOCK_CANCEL, GTK_RESPONSE_CANCEL, GTK_STOCK_OK, GTK_RESPONSE_OK, NULL);
	gtk_window_set_default_size(GTK_WINDOW(dialog), 400, -1);
	support_type_label = gtk_label_new("Mark all items that pertain to your issues.");
	network_toggle = gtk_check_button_new_with_label("Networking");
	sound_toggle = gtk_check_button_new_with_label("Sound");
	video_toggle = gtk_check_button_new_with_label("Video/Display");
	
	gtk_widget_show(support_type_label);
	gtk_widget_show(network_toggle);
	gtk_widget_show(sound_toggle);
	gtk_widget_show(video_toggle);
	
	gtk_box_pack_start(GTK_BOX(GTK_DIALOG(dialog)->vbox), support_type_label, TRUE, FALSE, 5);
	gtk_box_pack_start(GTK_BOX(GTK_DIALOG(dialog)->vbox), network_toggle, TRUE, FALSE, 5);
	gtk_box_pack_start(GTK_BOX(GTK_DIALOG(dialog)->vbox), sound_toggle, TRUE, FALSE, 5);
	gtk_box_pack_start(GTK_BOX(GTK_DIALOG(dialog)->vbox), video_toggle, TRUE, FALSE, 5);
	
	return dialog;
}

gint get_support_type_composite()
{
	gint composite = 0;
	
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
	return composite;
}
