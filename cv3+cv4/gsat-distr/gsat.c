#include <stdlib.h>             /* strtol */
#include <stdio.h>              /* printf */
#include <string.h>             /* strcmp */
#include <math.h>               /* isnan etc. */
#ifdef _MSC_VER
#include "getopt.h"
#include <windows.h>            /* ctrl c handler */
#undef max
#undef min
#else
#include <unistd.h>             /* getopt */
#include <limits.h>
#include <signal.h>
#endif
#include "sat_inst.h"
#include "sat_sol.h"
#include "rngctrl.h"
/*-----------------------------------------------------------------------------*/
char synopsis[] = "gsat <options> [dimacs-file]\n"
"\t Input format control\n"
"\t-w number                        max literals in a clause, default 3\n"
"\t Iteration control\n"
"\t-i number                        max iterations (flips)\n"
"\t-T number                        max tries (restarts)\n"
"\t-p number                        probability of a random step, float, 0..1.0\n"
"\t Output control (iteration count and sat clauses to stdout)\n"
"\t-d <file>                        output iteration log into <file>\n"
"\t-t <file>                        detailed trace into <file>\n"
"\t-D                               debug info to stderr\n"
"\t-e string                        resulting line specifier\n"
;
/*-----------------------------------------------------------------------------*/
/* global parametrs                                                            */
int cont=1;                         /* do continue iterating */
/*-----------------------------------------------------------------------------*/
/*  CTRL-C handler                                             */
/*-----------------------------------------------------------------------------*/
#ifdef _MSC_VER
BOOL WINAPI CtrlHandler(DWORD fdwCtrlType) {
    switch (fdwCtrlType) {
        
    case CTRL_CLOSE_EVENT:  /* CTRL-CLOSE: confirm that the user wants to exit. */
    case CTRL_C_EVENT:      /* Handle the CTRL-C signal. */
        cont = 0;
        return TRUE;
                
    case CTRL_BREAK_EVENT:  /* Pass other signals to the next handler. */
    case CTRL_LOGOFF_EVENT:
    case CTRL_SHUTDOWN_EVENT:
        cont = 0;
        return FALSE;
    default:
        return FALSE;
    }
}
#else
void handler (int signo) {
    cont = 0;
}
#endif
/*-----------------------------------------------------------------------------*/
/*      for all clauses in sol, update the number of true literals in cnt      */
/*-----------------------------------------------------------------------------*/
int gw_eval (sol_t sol, inst_t* inst, cnt_t cnt) {
    int sat = 0, i, v;
    literal_t* clause;
    for (i=0, clause=inst->body; i<inst->length; i++, clause+=inst->width) {
        cnt[i] = 0;
        for(v=0; v<inst->width; v++) {
    	    if (clause[v] != 0) cnt[i]+=sol[clause[v]];
        }
        if (cnt[i] > 0) sat++;
    }
    return sat;
}
/*-----------------------------------------------------------------------------*/
/*      build the var_info structure telling where each variable is used       */
/*-----------------------------------------------------------------------------*/
var_info_t gw_varinf_build (inst_t* inst) {
    var_info_t varinf;
    literal_t* clause;
    int i,v,l;
    varinf = calloc (inst->vars_no+1, sizeof(var_info));        /* item 0 is bogus */
    if (!varinf) return NULL;
    for (i=0, clause=inst->body; i<inst->length; i++, clause+=inst->width) {
        for(l=0; l<inst->width; l++) {
    	    if (clause[l] > 0) varinf[clause[l]].pos_occ_no++; else
    	    if (clause[l] < 0) varinf[-clause[l]].neg_occ_no++;
        }
    }
    for (v=1; v<=inst->vars_no; v++) {
        varinf[v].pos_occ = calloc (varinf[v].pos_occ_no, sizeof(clause_ix_t));
        varinf[v].pos_occ_no = 0;
        varinf[v].neg_occ = calloc (varinf[v].neg_occ_no, sizeof(clause_ix_t));
        varinf[v].neg_occ_no = 0;
    }
    for (i=0, clause=inst->body; i<inst->length; i++, clause+=inst->width) {
        for(l=0; l<inst->width; l++) {
    	    if (clause[l] > 0) {
    	        v=clause[l];
    	        varinf[v].pos_occ [varinf[v].pos_occ_no] = i; 
    	        varinf[v].pos_occ_no++; 
    	    } else
    	    if (clause[l] < 0) {
    	        v=-clause[l];
    	        varinf[v].neg_occ [varinf[v].neg_occ_no] = i; 
    	        varinf[v].neg_occ_no++; 
    	    }
        }
    }
    return varinf;
}
/*-----------------------------------------------------------------------------*/
/*      debug dump of the var_info structure to out                            */
/*-----------------------------------------------------------------------------*/
int gw_varinf_dump (var_info_t varinf,inst_t* inst, FILE* out) {
    int i,v;
    for (v=1; v<=inst->vars_no; v++) {
        fprintf(out,"%3d P %3d:", v, varinf[v].pos_occ_no); 
        for (i=0; i<varinf[v].pos_occ_no; i++) fprintf(out," %3d",varinf[v].pos_occ[i]);
        fprintf(out,"\n");
        fprintf(out,"%3d N %3d:", v, varinf[v].neg_occ_no); 
        for (i=0; i<varinf[v].neg_occ_no; i++) fprintf(out," %3d",varinf[v].neg_occ[i]);
        fprintf(out,"\n");
    }
    return 0;
}

/*-----------------------------------------------------------------------------*/
var_info_t gw_varinf_forget (var_info_t varinf, inst_t* inst) {
    int v;
    if (varinf) {
        for (v=1; v<=inst->vars_no; v++) {
            free (varinf[v].pos_occ);
            free (varinf[v].neg_occ); 
        }  
        free (varinf);
    }
    return NULL;
}
/*-----------------------------------------------------------------------------*/
/*      determine the change in satisfied clause number when variable v 1->0   */
/*-----------------------------------------------------------------------------*/
int gw_neg_flip_gain (var_info_t varinf, cnt_t cnt, int v) {
    int i, gain=0;
    for (i=0; i<varinf[v].pos_occ_no; i++) {    /* for all clauses where the variable occurs in a positive literal */
        if (cnt[varinf[v].pos_occ[i]] == 1) gain--;
    }
    for (i=0; i<varinf[v].neg_occ_no; i++) {    /* for all clauses where the variable occurs in a negative literal */
        if (cnt[varinf[v].neg_occ[i]] == 0) gain++;
    }
    return gain;
}
/*-----------------------------------------------------------------------------*/
/*      determine the change in satisfied clause number when variable v 0->1   */
/*-----------------------------------------------------------------------------*/
int gw_pos_flip_gain (var_info_t varinf, cnt_t cnt, int v) {
    int i, gain=0;
    for (i=0; i<varinf[v].pos_occ_no; i++) {    /* for all clauses where the variable occurs in a positive literal */
        if (cnt[varinf[v].pos_occ[i]] == 0) gain++;
    }
    for (i=0; i<varinf[v].neg_occ_no; i++) {    /* for all clauses where the variable occurs in a negative literal */
        if (cnt[varinf[v].neg_occ[i]] == 1) gain--;
    }
    return gain;
}
/*-----------------------------------------------------------------------------*/
/*   determine which variable flip gives the max gain                          */
/*   should return a list and pick randomly                                    */
/*-----------------------------------------------------------------------------*/
int gw_max_flip_var (var_info_t varinf, inst_t* inst, cnt_t cnt, sol_t sol) {
    int maxflip, maxgain, v, gain;
    maxflip = 0; maxgain = INT_MIN;
    for (v=1; v<=inst->vars_no; v++) {
        gain = sol[v] ? gw_neg_flip_gain (varinf, cnt, v) : gw_pos_flip_gain (varinf, cnt, v);
        if (gain > maxgain) { maxflip = v; maxgain = gain; }
        /* fprintf(stderr,"%d %s flip, gain: %d\n", v, (sol[v] ? "neg" : "pos"), gain); */
    }
    return maxflip;
}
/*-----------------------------------------------------------------------------*/
/*      realize flip 1->0 of variable v, update cnt                            */
/*-----------------------------------------------------------------------------*/
int gw_make_neg_flip (var_info_t varinf, cnt_t cnt, int v) {
    int i, gain=0;
    for (i=0; i<varinf[v].pos_occ_no; i++) {    /* for all clauses where the variable occurs in a positive literal */
        if (cnt[varinf[v].pos_occ[i]] == 1) gain--;
        cnt[varinf[v].pos_occ[i]]--;
    }
    for (i=0; i<varinf[v].neg_occ_no; i++) {    /* for all clauses where the variable occurs in a negative literal */
        if (cnt[varinf[v].neg_occ[i]] == 0) gain++;
        cnt[varinf[v].neg_occ[i]]++;
    }
    return gain;
}
/*-----------------------------------------------------------------------------*/
/*      realize flip 0->1 of variable v, update cnt                            */
/*-----------------------------------------------------------------------------*/
int gw_make_pos_flip (var_info_t varinf, cnt_t cnt, int v) {
    int i, gain=0;
    for (i=0; i<varinf[v].pos_occ_no; i++) {    /* for all clauses where the variable occurs in a positive literal */
        if (cnt[varinf[v].pos_occ[i]] == 0) gain++;     /* it is a waste to compute gain again */
        cnt[varinf[v].pos_occ[i]]++;
    }
    for (i=0; i<varinf[v].neg_occ_no; i++) {    /* for all clauses where the variable occurs in a negative literal */
        if (cnt[varinf[v].neg_occ[i]] == 1) gain--;
        cnt[varinf[v].neg_occ[i]]--;
    }
    return gain;
}
/*-----------------------------------------------------------------------------*/
/*      realize flip 1->0 of variable v, update cnt                            */
/*-----------------------------------------------------------------------------*/
int gw_make_flip (var_info_t varinf, inst_t* inst, cnt_t cnt, sol_t sol, int v) {
    int gain=0;
    if (sol[v]) {
        gain += gw_make_neg_flip (varinf, cnt, v);    /* update true literal counters */
    } else {
        gain += gw_make_pos_flip (varinf, cnt, v);
    }
    sol_flip (sol, v);
    return gain;
}
/*-----------------------------------------------------------------------------*/
/*      randomly choose an unsatisfied clause                                  */
/*-----------------------------------------------------------------------------*/
int gw_pick_unsat (inst_t* inst, cnt_t cnt, int satisfied) {
    unsigned c; int i,pick;
    c = rng_next_range(1, inst->length-satisfied);
    pick=0;
    for (i=0; i<inst->length; i++) {
        if (cnt[i] == 0) {
            pick++;
            if (pick == c) return i;
        }
    }
    return 0;
}
/*-----------------------------------------------------------------------------*/
/*      randomly choose a variable in a clause                                 */
/*-----------------------------------------------------------------------------*/
int gw_pick_var (inst_t* inst, cnt_t cnt, int cli) {
    literal_t* clause;
    int pick,i;

    clause = inst->body+cli*inst->width;
    for (i=0; i<inst->width; i++) if (clause[i] == 0) break;
    pick = rng_next_range(0, i-1);
    if (clause[pick] < 0) return -clause[pick];
    return clause[pick];
}
/*-----------------------------------------------------------------------------*/
int main (int argc, char** argv) {
    /* parameters and default values*/
    int     width=3;
    int     itrmax=300; /* max iterations */
    int     triesmax=1; /* max tries */
    double  p=0.4;      /* gredy / random probability */
    int     debug=0;    /* debug info to stderr */
    char*   datafile=NULL;  FILE* data=NULL;   /* sat clauses versus iteration no. */
    char*   tracefile=NULL; FILE* trace=NULL;  /* detailed trace */
    char*   infile=NULL;    FILE* in=NULL;     /* input */
    const char* outsep=" ";                    /* output separator */   

    int     err=0;      /* err indicator */
    char* epf; char opt;/* options scanning */
    inst_t  inst;       /* instance */
    sol_t   sol;        /* solution */
    cnt_t   cnt=NULL;   /* true literals counters, per clause */
    int     satisfied;  /* current no. of sat clauses */ 
    int     flipvar;    /* max gain or picked flipping variable */
    int     ucli;       /* picked unsat clause */
    int     gain;       /* flip gain */
    var_info_t varinf;  /* inverted instance */
    int     itrno;      /* iteration number within a try */
    int     tryno;	    /* number of restarts */
    double  dec;        /* greedy / random decision */
    char*   itype;      /* greedy or random */
    /* --------------------- CTRL-C handling ---------------- */
    
#ifdef _MSC_VER
    if (! SetConsoleCtrlHandler(CtrlHandler, TRUE)) { 
        fprintf (stderr, "%s: cannot establish a signal handler\n", argv[0]); 
        err++; 
    }
#else
    struct sigaction act = { 0 };

    act.sa_flags = SA_RESTART;
    act.sa_handler = &handler;

    if (sigaction(SIGINT,&act,NULL) != 0) {
        fprintf (stderr, "%s: cannot establish a signal handler\n", argv[0]); 
        err++; 
    }
#endif
    /* ---------------------- options ----------------------- */
    while ((opt = getopt(argc, argv, "T:t:d:Di:p:w:r:R:s:S:e:")) != -1) {
         switch (opt) {
         case 'd': datafile = optarg; break;    /* datafile required */
         case 't': tracefile = optarg; break;   /* trace required */
         case 'e': outsep = optarg; break;      /* separator */
         case 'D': debug=1; break;              /* debugging required */
         case 'p': p = strtod(optarg, &epf);    /* probability of random steps in an iteration */
                   if (*epf != 0)          { fprintf (stderr, "%s: the arg to -p should be numeric\n", argv[0]); err++; }
                   if (p < 0.0 || p > 1.0) { fprintf (stderr, "%s: the arg to -p should be between 0 and 1\n", argv[0]); err++; }
                   break;
         case 'w': width = strtol(optarg, &epf, 0); /* max clause length - needed when input from stdin */
                   if (*epf != 0) { fprintf (stderr, "%s: the arg to -w should be numeric\n", argv[0]); err++; }
                   if (width <= 0) { fprintf (stderr, "%s: the arg to -w should be positive\n", argv[0]); err++; }
                   break;
         case 'i': itrmax = strtol(optarg, &epf, 0);    /* max no. of iteration - 0 means no limit */
                   if (*epf != 0) { fprintf (stderr, "%s: the arg to -i should be numeric\n", argv[0]); err++; }
                   if (itrmax < 0) { fprintf (stderr, "%s: the arg to -i should be positive or zero\n", argv[0]); err++; }
                   break;
         case 'T': triesmax = strtol(optarg, &epf, 0);    /* max no. of tries - 0 means no limit */
                   if (*epf != 0) { fprintf (stderr, "%s: the arg to -T should be numeric\n", argv[0]); err++; }
                   if (triesmax < 0) { fprintf (stderr, "%s: the arg to -T should be positive or zero\n", argv[0]); err++; }
                   break;
         case 'r':      /* PRNG controls */
         case 'R': 
	     case 's':
         case 'S': if (!rng_options (opt, optarg, argv[0])) err++;
                   break;
         default:  fprintf (stderr, "%s%s", synopsis, rng_synopsis); 
                   return EXIT_FAILURE;  /* unknown parameter, e.g. -h */
         }
    }
    if (optind < argc) infile = argv[optind];                       /* input file on the command line */
    if (err) return EXIT_FAILURE;                                   /* stop here if any error */

    /* ----------------- RNG controls ------------------------ */
    if (!rng_apply_options (argv[0])) return EXIT_FAILURE;          /* errors are reported already */
    
    /* ----------------------- instance input ---------------- */
    if (infile) {
        in = fopen(infile, "r");                                    /* try to determine the width from input */
        if (!in) { perror(infile); return EXIT_FAILURE; }
        width = inst_width(&inst, in);
        if (width < 0) {
            err = width;                                            /* failed */
        } else {
            rewind(in);                                             /* reopen input for CNF reading */
        }
    } else { 
        in = stdin;                                                 /* no file, read stdin */
    }
    if (!err) err = inst_read(&inst, in, width);                    /* if any error so far, report and exit */
    if (err) {
        switch (err) {
        case ERR_PROBLEM: fprintf (stderr, "%s: problem type not a CNF\n", argv[0]); break;
        case ERR_FORMAT:  fprintf (stderr, "%s: input not in DIMACS file format\n", argv[0]); break;
        case ERR_WIDTH:   fprintf (stderr, "%s: clause width exceeded\n", argv[0]); break;
        case ERR_ALLOC:   fprintf (stderr, "%s: allocation failure\n", argv[0]); break;
        default: break;
        }
        return EXIT_FAILURE;
    }
    
    if (datafile) {
        if (strcmp (datafile, "-") == 0) {                          /* datafile requested to stderr */
            data = stderr;
        } else {
            data = fopen(datafile, "w");                            /* datafile is a real file */
            if (!data) { perror(datafile); return EXIT_FAILURE; }
        }
    }
    if (tracefile) {
        if (strcmp (tracefile, "-") == 0) {                         /* trace requested to stderr */
            trace = stderr;
        } else {
            trace = fopen(tracefile, "w");                          /* tracefile is a real file */
            if (!trace) { perror(tracefile); return EXIT_FAILURE; }
        }
    }
/*  inst_write(&inst, stderr); */

    /* ----------------------- instance inversion ------------- */
    if (!(varinf = gw_varinf_build (&inst))) {                      /* build the 'where used' structure */
        fprintf (stderr, "%s: allocation failure\n", argv[0]); return EXIT_FAILURE;
    }	
    if (debug) gw_varinf_dump (varinf, &inst, stderr);

    /* ----------------------- solution  space  --------------- */
    if (!(sol = sol_reserve(inst.vars_no))) {                       /* build the solution arrray  */
        fprintf (stderr, "%s: allocation failure\n", argv[0]); return EXIT_FAILURE;
    }	

    tryno = 1;
    itrno = 0; 
    satisfied = 0;
    while (satisfied < inst.length && cont && ((!triesmax) || tryno <= triesmax)) {

        sol_rand (sol, inst.vars_no);                                   /* random 0/1 assignment */
        /* ----------------------- evaluation --------------------- */
        if (!(cnt = cnt_reserve(inst.length))) {                        /* build the array of true literal counts */
            fprintf (stderr, "%s: allocation failure\n", argv[0]); return EXIT_FAILURE;
        }	
        satisfied = gw_eval (sol, &inst, cnt);                          /* evaluate true literals and count sat clauses */
    
        /* ----------------------- debug and trace ---------------- */
        if (data) fprintf (data, "%d %d\n", 0, satisfied);
        if (debug) {
            sol_write(sol, stderr, inst.vars_no); 
            fprintf(stderr,"satisfied: %d\n",satisfied);
            for (int i=0; i<inst.length; i++) fprintf(stderr, " %d", cnt[i]); 
            fprintf(stderr, "\n");
        }
        if (trace) { 
            fprintf (trace, "initial: satisfied %d, solution: ", satisfied);
            sol_write(sol, trace,  inst.vars_no); 
            fprintf (trace, "true literals: ");
            for (int i=0; i<inst.length; i++) fprintf(trace, " %d", cnt[i]); 
            fprintf(trace, "\n");
        }
        /* ----------------------- gsat inner iteration ----------- */
        itrno = 1; gain=1;                                              /* stop when formula satisfied, CTRL-C occurs */
                                                                    /* and then either iterations unlimited or still below limit */
        while (satisfied < inst.length && cont && ((!itrmax) || itrno <= itrmax)) {
            dec = rng_next_double();                                    /* choose a greedy or random step */
            if (dec > p) {                                              /* greedy */
                flipvar = gw_max_flip_var (varinf, &inst, cnt, sol);    /* select the var with max gain to flip */
                gain = gw_make_flip (varinf, &inst, cnt, sol, flipvar); /* update the true literals counters, determine gain */
                itype = "greedy";
            } else {
                ucli = gw_pick_unsat (&inst, cnt, satisfied);           /* pick some unsat clause at random */
                flipvar = gw_pick_var (&inst, cnt, ucli);               /* pick a variable in that clause */
                gain = gw_make_flip (varinf, &inst, cnt, sol, flipvar); /* update the true literals counters, determine gain */
                itype = "random";
            }       
            satisfied += gain;                                          /* update sat clauses no. */
            if (data) fprintf (data, "%d %d\n", itrno, satisfied);      /* datafile line */
            if (debug) {                                                /* debug info */
                fprintf(stderr,"%s flipvar %d, satisfied: %d\n",itype, flipvar, satisfied);
            }
            if (trace) {                                                /* readable trace info */
                fprintf (trace, "itr %d, %s, flipvar %d, satisfied %d, solution: ", itrno, itype, flipvar, satisfied);
                sol_write(sol, trace,  inst.vars_no); 
                fprintf (trace, "true literals: ");
                for (int i=0; i<inst.length; i++) fprintf(trace, " %d", cnt[i]); 
                fprintf(trace, "\n");
            }
            itrno++;
        }
        tryno++;
    }
    fprintf (stderr, "%d%s%d%s%d%s%d\n", (tryno-2)*itrmax+itrno-1, outsep, triesmax*itrmax, outsep, satisfied, outsep, inst.length);    /* final information */
    sol_write (sol, stdout, inst.vars_no);
    rng_end_options (argv[0]);
    
    varinf = gw_varinf_forget(varinf, &inst);
    cnt = cnt_forget(cnt);
    sol = sol_forget(sol, inst.vars_no);
    inst_forget(&inst);
    
    if (datafile && strcmp (datafile, "-") != 0) fclose (data);
    if (tracefile && strcmp (tracefile, "-") != 0) fclose (trace);
    if (infile) fclose (in);
    
    return EXIT_SUCCESS;
}
