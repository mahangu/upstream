/*	Author: Ryan Zeigler
	This file is part of Upstream the log submission system.
	This file is released under the GPL
*/

#include <gtk/gtk.h>
#include <stdio.h>

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
	gchar* email_addr;
	gchar* support_msg;
	
	gtk_init_check(&argc, &argv);

	if(argc == 2 && !strcmp(argv[1], "-h"))
	{
		g_print("Usage: canoe /path/to/upstream.py (optional)\n");
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
		g_print("Email: %s\n", email_addr);
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
		g_print("Support message: %s\n", support_msg);
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
	network_toggle = gtk_check_button_new_with_label("network_toggle");
	sound_toggle = gtk_check_button_new_with_label("sound_toggle");
	video_toggle = gtk_check_button_new_with_label("video_toggle");
	
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
	gint composite;
	if(gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(network_toggle)))
	{
		composite = composite & network;
	}
	if(gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(sound_toggle)))
	{
		composite = composite & sound;
	}
	if(gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(video_toggle)))
	{
		composite = composite & video;
	}
	return composite;
}
